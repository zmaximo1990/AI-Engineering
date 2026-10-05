import logging
from typing import Optional

from llm import AnthropicClient, BaseLLMClient, GeminiClient, OpenAIClient
from schemas import LLMConfig, Provider

logger = logging.getLogger(__name__)

class LLMFactory():

    @staticmethod
    def create_client(config: LLMConfig) -> BaseLLMClient:
        """Factory that builds an LLM client from an LLMConfig."""
        logger.info("Creating LLM client for provider=%s", config.provider.value)

        kwargs = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }

        client: Optional[BaseLLMClient] = None
        if config.provider == Provider.OPENAI:
            client = OpenAIClient(**kwargs)
        elif config.provider == Provider.ANTHROPIC:
            client = AnthropicClient(**kwargs)
        elif config.provider == Provider.GEMINI:
            client = GeminiClient(**kwargs)
        else:
            raise ValueError(f"Invalid provider: {config.provider}")
        logger.info("LLM client created: %s", type(client).__name__)
        return client
