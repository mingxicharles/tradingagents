"""
API Configuration Module
Handles API key setup and validation
"""
import os
from typing import Optional


def set_openai_api_key(api_key: str) -> None:
    """
    Set OpenAI API key in environment
    
    Args:
        api_key: Your OpenAI API key
    """
    os.environ["OPENAI_API_KEY"] = api_key
    print(f"✓ OpenAI API key configured (ends with ...{api_key[-4:]})")


def set_local_model(model_name: str = "Qwen/Qwen2.5-7B-Instruct") -> None:
    """
    Configure to use local model instead of API
    
    Args:
        model_name: HuggingFace model name
    """
    os.environ["USE_LOCAL_MODEL"] = "true"
    os.environ["LOCAL_MODEL"] = model_name
    print(f"✓ Configured to use local model: {model_name}")


def set_openrouter_api_key(api_key: str, model: str = "openai/gpt-3.5-turbo") -> None:
    """
    Set OpenRouter API key and model
    
    Args:
        api_key: Your OpenRouter API key
        model: Model to use (default: openai/gpt-3.5-turbo)
               Popular options: 
               - openai/gpt-4
               - anthropic/claude-2
               - google/palm-2-chat-bison
               - meta-llama/llama-2-70b-chat
    """
    os.environ["USE_OPENROUTER"] = "true"
    os.environ["OPENROUTER_API_KEY"] = api_key
    os.environ["OPENROUTER_MODEL"] = model
    print(f"✓ OpenRouter configured")
    print(f"  Model: {model}")
    print(f"  API Key: ...{api_key[-4:]}")


def get_api_key() -> Optional[str]:
    """
    Get current API key from environment
    
    Returns:
        API key or None if not set
    """
    return os.environ.get("OPENAI_API_KEY")


def is_api_configured() -> bool:
    """
    Check if API is properly configured
    
    Returns:
        True if API key is set or using local model
    """
    has_api_key = bool(os.environ.get("OPENAI_API_KEY"))
    use_local = os.environ.get("USE_LOCAL_MODEL", "false").lower() == "true"
    
    return has_api_key or use_local


def validate_api_setup() -> tuple[bool, str]:
    """
    Validate API configuration
    
    Returns:
        (is_valid, message) tuple
    """
    use_local = os.environ.get("USE_LOCAL_MODEL", "false").lower() == "true"
    use_openrouter = os.environ.get("USE_OPENROUTER", "false").lower() == "true"
    
    if use_local:
        model = os.environ.get("LOCAL_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        return True, f"Using local model: {model}"
    
    if use_openrouter:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
        if not api_key:
            return False, "OpenRouter API key not set. Use set_openrouter_api_key() or set environment variable."
        return True, f"Using OpenRouter API with model: {model}"
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return False, "OpenAI API key not set. Use set_openai_api_key() or set environment variable."
    
    if len(api_key) < 20:
        return False, "API key seems invalid (too short)"
    
    return True, f"Using OpenAI API (key ends with ...{api_key[-4:]})"


def print_api_status() -> None:
    """Print current API configuration status"""
    use_local = os.environ.get("USE_LOCAL_MODEL", "false").lower() == "true"
    use_openrouter = os.environ.get("USE_OPENROUTER", "false").lower() == "true"
    
    print("=" * 60)
    print("API Configuration Status")
    print("=" * 60)
    
    if use_local:
        model = os.environ.get("LOCAL_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        print(f"Mode: Local Model")
        print(f"Model: {model}")
    elif use_openrouter:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
        if api_key:
            print(f"Mode: OpenRouter API")
            print(f"Model: {model}")
            print(f"API Key: ...{api_key[-4:]}")
        else:
            print(f"Mode: OpenRouter API")
            print(f"API Key: NOT SET ❌")
            print("\nTo configure:")
            print("  from tradingagents.config_api import set_openrouter_api_key")
            print("  set_openrouter_api_key('your-api-key', 'openai/gpt-4')")
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            print(f"Mode: OpenAI API")
            print(f"API Key: ...{api_key[-4:]}")
        else:
            print(f"Mode: OpenAI API")
            print(f"API Key: NOT SET ❌")
            print("\nTo configure:")
            print("  from tradingagents.config_api import set_openai_api_key")
            print("  set_openai_api_key('your-api-key')")
    
    print("=" * 60)

