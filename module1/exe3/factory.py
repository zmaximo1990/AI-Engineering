import logging

from llm import AnthropicClient, BaseLLMClient, GeminiClient, OpenAIClient
from schemas import LLMConfig, Provider

logger = logging.getLogger(__name__)


def create_llm_client(config: LLMConfig) -> BaseLLMClient:
    """Factory that builds an LLM client from an LLMConfig."""
    logger.info("Creating LLM client for provider=%s", config.provider.value)

    kwargs = {
        "model": config.model,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
    }

    if config.provider is Provider.OPENAI:
        client = OpenAIClient(**kwargs)
    elif config.provider is Provider.ANTHROPIC:
        client = AnthropicClient(**kwargs)
    elif config.provider is Provider.GEMINI:
        client = GeminiClient(**kwargs)
    else:
        raise ValueError(f"Unsupported provider: {config.provider!r}")

    logger.info("LLM client created: %s", type(client).__name__)
    return client
