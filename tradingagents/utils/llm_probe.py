from __future__ import annotations

import asyncio
from typing import Any, Dict

from ..llm import build_client, resolve_llm_config


async def probe_llm(**completion_kwargs: Any) -> Dict[str, Any]:
    """Inspect resolved LLM configuration and attempt a lightweight completion."""
    config = resolve_llm_config()
    client = build_client()
    result: Dict[str, Any] = {
        "provider": config.provider,
        "base_url": config.base_url,
        "model": config.model,
    }
    try:
        response = await client.retrying_complete(
            [{"role": "user", "content": "Reply with the word 'ready'"}],
            attempts=1,
            max_tokens=4,
            **completion_kwargs,
        )
        result["status"] = "ok"
        result["response"] = response
    except Exception as err:  # pragma: no cover - diagnostic tool
        result["status"] = "error"
        result["error"] = repr(err)
    return result


async def _async_main() -> None:
    info = await probe_llm()
    print("LLM probe result:")
    for key, value in info.items():
        print(f"  {key}: {value}")


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
