import logging
from typing import Any

from llm import BaseLLMClient, OpenAIClient, AnthropicClient, GeminiClient

logger = logging.getLogger(__name__)


def create_llm_client(config: dict[str, Any]) -> BaseLLMClient:
    """Factory that builds an LLM client from a provider config.

    Expected config keys:
      - provider: "openai" | "anthropic"
      - model (optional)
      - max_tokens (optional)
    """
    provider = (config.get("provider") or "").strip().lower()
    model = config.get("model")
    max_tokens = config.get("max_tokens")

    logger.info("Creating LLM client for provider=%s", provider)

    kwargs: dict[str, Any] = {}
    if model is not None:
        kwargs["model"] = model
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    if provider == "openai":
        client = OpenAIClient(**kwargs)
    elif provider == "anthropic":
        client = AnthropicClient(**kwargs)
    elif provider == "gemini":
        client = GeminiClient(**kwargs)
    else:
        raise ValueError(
            f"Unsupported provider: {provider!r}. Use 'openai' or 'anthropic'."
        )

    logger.info("LLM client created: %s", type(client).__name__)
    return client
