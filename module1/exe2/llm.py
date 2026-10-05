import logging
import os
from abc import ABC, abstractmethod

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from google import genai
from pydantic import SecretStr

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Common interface for LLM providers."""

    default_model: str

    @abstractmethod
    async def chat(self, message: str) -> str:
        """Send a message entered by the user to the model and return the response text."""
        ...


class OpenAIClient(BaseLLMClient):
    default_model: str = "gpt-4o-mini"

    def __init__(self, model: str = None, max_tokens: int = 256) -> None:
        self.model = model or self.default_model
        self.max_tokens = max_tokens
        api_key = SecretStr(os.environ.get("OPENAI_API_KEY", ""))
        self._client = AsyncOpenAI(api_key=api_key.get_secret_value())
        logger.info("OpenAIClient initialized (model=%s)", self.model)

    async def chat(self, message: str) -> str:
        logger.info("OpenAIClient.chat started")
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": message}],
            max_tokens=self.max_tokens,
        )
        content = response.choices[0].message.content or ""
        logger.info("OpenAIClient.chat finished (%d chars)", len(content))
        return content


class AnthropicClient(BaseLLMClient):
    default_model: str = "claude-haiku-4-5-20251001"

    def __init__(
        self, model: str = None, max_tokens: int = 256
    ) -> None:
        self.model = model or self.default_model
        self.max_tokens = max_tokens
        api_key = SecretStr(os.environ.get("ANTHROPIC_API_KEY", ""))
        self._client = AsyncAnthropic(api_key=api_key.get_secret_value())
        logger.info("AnthropicClient initialized (model=%s)", self.model)

    async def chat(self, message: str) -> str:
        logger.info("AnthropicClient.chat started")
        response = await self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": message}],
        )
        content = response.content[0].text if response.content else ""
        logger.info("AnthropicClient.chat finished (%d chars)", len(content))
        return content

class GeminiClient(BaseLLMClient):
    default_model: str = "models/gemini-3.8-flash"

    def __init__(
        self,
        model: str | None = None,
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> None:
        self.model = model or self.default_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        api_key = SecretStr(os.environ.get("GEMINI_API_KEY", ""))
        self._client = genai.Client(api_key=api_key.get_secret_value())
        logger.info("GeminiClient initialized (model=%s)", self.model)

    def _create_chat(self):
        return self._client.aio.chats.create(
            model=self.model,
            config={
                "max_output_tokens": self.max_tokens,
                "temperature": self.temperature,
            },
        )

    async def chat(self, message: str) -> str:
        logger.info("GeminiClient.chat started")
        session = self._create_chat()
        response = await session.send_message(message)
        content = response.text or ""
        logger.info("GeminiClient.chat finished (%d chars)", len(content))
        return content