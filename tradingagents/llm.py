from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency optional until installed
    load_dotenv = None

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - optional dependency guard
    AsyncOpenAI = None  # type: ignore[assignment]

if load_dotenv is not None:
    load_dotenv(override=False)

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
except ImportError:
    torch = None  # type: ignore[assignment]
    AutoModelForCausalLM = None  # type: ignore[assignment]
    AutoTokenizer = None  # type: ignore[assignment]
    TextIteratorStreamer = None  # type: ignore[assignment]

def _infer_default_model() -> str:
    if os.environ.get("OPENAI_MODEL"):
        return os.environ["OPENAI_MODEL"]
    if os.environ.get("LLM_MODEL"):
        return os.environ["LLM_MODEL"]
    if os.environ.get("OPENAI_API_KEY"):
        return "gpt-4o-mini"
    return os.environ.get("LOCAL_MODEL", "Qwen/Qwen2.5-7B-Instruct")


def _infer_default_base_url() -> str:
    if os.environ.get("LLM_BASE_URL"):
        return os.environ["LLM_BASE_URL"]
    if os.environ.get("OPENAI_BASE_URL"):
        return os.environ["OPENAI_BASE_URL"]
    if os.environ.get("OPENROUTER_BASE_URL"):
        return os.environ["OPENROUTER_BASE_URL"]
    if os.environ.get("OPENAI_API_KEY"):
        return "https://api.openai.com/v1"
    if os.environ.get("OPENROUTER_API_KEY"):
        return "https://openrouter.ai/api/v1"
    return "https://api.openai.com/v1"


DEFAULT_MODEL = _infer_default_model()
DEFAULT_BASE_URL = _infer_default_base_url()
USE_LOCAL_MODEL = os.environ.get("USE_LOCAL_MODEL", "false").lower() == "true"
USE_OPENROUTER = os.environ.get("USE_OPENROUTER", "false").lower() == "true"


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class LLMConfig:
    provider: str
    base_url: str
    model: str
    api_key: Optional[str]
    headers: Dict[str, str]


def _mask_key(key: Optional[str]) -> str:
    if not key:
        return "missing"
    if len(key) <= 8:
        return f"{key[:2]}…{key[-2:]}"
    return f"{key[:4]}…{key[-4:]}"


def resolve_llm_config() -> LLMConfig:
    base_url = _infer_default_base_url().strip()
    base_url = base_url or "https://api.openai.com/v1"
    provider = "openrouter" if "openrouter.ai" in base_url else "openai"

    openai_key = os.environ.get("OPENAI_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    api_key: Optional[str]

    if provider == "openrouter":
        api_key = openrouter_key
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY must be set when using OpenRouter.")
    else:
        api_key = openai_key
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY must be set when using the OpenAI API.")

    model = _infer_default_model()
    if provider == "openrouter" and "/" not in model:
        model = f"openai/{model}"

    headers: Dict[str, str] = {}
    if provider == "openrouter":
        referer = os.environ.get("OPENROUTER_REFERER")
        title = os.environ.get("OPENROUTER_APP_TITLE")
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title

    return LLMConfig(
        provider=provider,
        base_url=base_url,
        model=model,
        api_key=api_key,
        headers=headers,
    )


class LocalLLMClient:
    """Local HuggingFace model client using transformers."""

    def __init__(self, model_name: str, use_flash_attention: bool = True) -> None:
        if AutoModelForCausalLM is None or AutoTokenizer is None:
            raise RuntimeError("Install 'transformers' and 'torch' to use local models.")
        
        print(f"Loading local model: {model_name}")
        self.device = "cuda" if torch and torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
        )
        
        # Load model with appropriate settings
        load_kwargs = {
            "device_map": "auto",
            "trust_remote_code": True,
        }
        
        # Add quantization for large models if GPU available
        if self.device == "cuda" and hasattr(torch, "float16"):
            load_kwargs["torch_dtype"] = torch.float16
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            **load_kwargs
        )
        
        # Enable eval mode
        self.model.eval()
        
        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        print("Model loaded successfully!")

    def _format_messages(self, messages: List[Mapping[str, str]]) -> str:
        """Convert OpenAI-style messages to model format."""
        # For Qwen models, use their chat template
        if hasattr(self.tokenizer, "apply_chat_template"):
            formatted = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            return formatted
        else:
            # Fallback for other models
            result = ""
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "system":
                    result += f"System: {content}\n\n"
                elif role == "user":
                    result += f"User: {content}\n\n"
                elif role == "assistant":
                    result += f"Assistant: {content}\n\n"
            return result

    async def complete(
        self,
        messages: List[Mapping[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 900,
        **kwargs: Any,
    ) -> str:
        """Generate completion asynchronously."""
        # Run generation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self._generate_sync,
            messages,
            temperature,
            max_tokens,
            kwargs
        )
        return result

    def _generate_sync(
        self,
        messages: List[Mapping[str, str]],
        temperature: float,
        max_tokens: int,
        kwargs: Dict[str, Any],
    ) -> str:
        """Synchronous generation method."""
        # Format messages
        prompt = self._format_messages(messages)
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        # Generation parameters
        gen_kwargs = {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "do_sample": temperature > 0,
            "pad_token_id": self.tokenizer.eos_token_id,
            **kwargs,
        }
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                **gen_kwargs
            )
        
        # Decode response (skip the prompt)
        generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
        response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        return response.strip()

    async def retrying_complete(
        self,
        messages: List[Mapping[str, str]],
        attempts: int = 2,
        backoff: float = 1.5,
        **kwargs: Any,
    ) -> str:
        """Complete with retry logic."""
        last_error: Optional[BaseException] = None
        for attempt in range(attempts):
            try:
                return await self.complete(messages, **kwargs)
            except Exception as err:
                last_error = err
                if attempt < attempts - 1:
                    await asyncio.sleep(backoff * (attempt + 1))
        raise RuntimeError(f"LLM request failed after {attempts} attempts") from last_error


class APILLMClient:
    """OpenAI-compatible API client (OpenRouter, etc.)."""

    def __init__(
        self,
        *,
        config: Optional[LLMConfig] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **default_kwargs: Any,
    ) -> None:
        if AsyncOpenAI is None:
            raise RuntimeError("Install the 'openai' package to use API client.")

        cfg = config or resolve_llm_config()
        resolved_base_url = base_url or cfg.base_url
        resolved_model = model or cfg.model
        resolved_api_key = api_key or cfg.api_key

        if "openrouter.ai" in resolved_base_url and "/" not in resolved_model:
            resolved_model = f"openai/{resolved_model}"

        if not resolved_api_key:
            raise RuntimeError("An API key must be supplied for API access.")

        headers = dict(default_kwargs.pop("default_headers", {}))
        if "openrouter" in resolved_base_url:
            referer = os.environ.get("OPENROUTER_REFERER")
            title = os.environ.get("OPENROUTER_APP_TITLE")
            if referer and "HTTP-Referer" not in headers:
                headers["HTTP-Referer"] = referer
            if title and "X-Title" not in headers:
                headers["X-Title"] = title

            if referer:
                headers["HTTP-Referer"] = referer
            if title:
                headers["X-Title"] = title

        self.provider = "openrouter" if "openrouter.ai" in resolved_base_url else "openai"
        self.base_url = resolved_base_url
        self.model = resolved_model
        self._client = AsyncOpenAI(
            base_url=resolved_base_url,
            **({"api_key": resolved_api_key} if resolved_api_key else {}),
            default_headers=headers or None,
        )
        self._default_kwargs = default_kwargs

    async def complete(
        self,
        messages: List[Mapping[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 900,
        **kwargs: Any,
    ) -> str:
        params = dict(self._default_kwargs)
        params.update(kwargs)
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **params,
        )
        if not response.choices:
            raise RuntimeError("Empty completion from LLM.")
        return response.choices[0].message.content or ""

    async def retrying_complete(
        self,
        messages: List[Mapping[str, str]],
        attempts: int = 2,
        backoff: float = 1.5,
        **kwargs: Any,
    ) -> str:
        last_error: Optional[BaseException] = None
        for attempt in range(attempts):
            try:
                return await self.complete(messages, **kwargs)
            except Exception as err:
                last_error = err
                if attempt < attempts - 1:
                    await asyncio.sleep(backoff * (attempt + 1))
        raise RuntimeError(f"LLM request failed after {attempts} attempts") from last_error


# Type alias for compatibility
LLMClient = LocalLLMClient | APILLMClient


def build_client() -> LLMClient:
    """Construct client instance using environment configuration."""
    if USE_LOCAL_MODEL:
        model_name = os.environ.get("LOCAL_MODEL", DEFAULT_MODEL)
        print(f"Building LOCAL model client: {model_name}")
        return LocalLLMClient(model_name)
    else:
        config = resolve_llm_config()
        print(f"Resolved LLM provider: {config.provider}")
        print(f"Using base URL: {config.base_url}")
        print(f"Model: {config.model}")
        print(f"API key: {_mask_key(config.api_key)}")
        return APILLMClient(config=config)


# Alias for backward compatibility
build_llm_client = build_client
