import logging
import os
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from anthropic import AnthropicError, AsyncAnthropic
from google import genai
from google.genai.errors import APIError as GeminiAPIError
from openai import AsyncOpenAI, OpenAIError
from pydantic import SecretStr
from decorators import anthropic_sem, gemini_sem, openai_sem, limit_concurrency, timeout
from schemas import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    ChatMessage,
    ModelResponse,
    Provider,
    Role,
)

logger = logging.getLogger(__name__)

class BaseLLMClient(ABC):
    """Common interface for LLM providers."""

    default_model: str
    provider: Provider
    api_key_env: str

    @abstractmethod
    async def chat(self, messages: list[ChatMessage]) -> ModelResponse:
        """Send a conversation to the model and return a ModelResponse."""
        ...

    @abstractmethod
    async def chat_stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        """Stream response chunks for a conversation."""
        ...

    def _require_api_key(self) -> SecretStr:
        """Return the API key from the environment, or raise if it is missing/empty."""
        value = os.environ.get(self.api_key_env, "").strip()
        if not value:
            raise ValueError(
                f"{self.api_key_env} is not configured. "
                "Set it in the environment before using this provider."
            )
        return SecretStr(value)

    def _success_response(self, content: str) -> ModelResponse:
        return ModelResponse(
            provider=self.provider,
            model=self.model,
            content=content,
        )

    def _error_response(self, error: Exception) -> ModelResponse:
        logger.exception("%s.chat failed", type(self).__name__)
        return ModelResponse(
            provider=self.provider,
            model=self.model,
            error=str(error),
        )

    @staticmethod
    def _system_text(messages: list[ChatMessage]) -> str | None:
        """
        Returns the system instruction from the messages, if any.
        """

        parts = [m.content for m in messages if m.role is Role.SYSTEM]
        return "\n\n".join(parts) if parts else None

    @staticmethod
    def _conversation(messages: list[ChatMessage]) -> list[ChatMessage]:
        """
        Returns the conversation from the messages, excluding the system instruction.
        """

        return [m for m in messages if m.role is not Role.SYSTEM]


class OpenAIClient(BaseLLMClient):
    default_model: str = "gpt-4o-mini"
    provider: Provider = Provider.OPENAI
    api_key_env: str = "OPENAI_API_KEY"

    def __init__(
        self,
        model: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float | None = DEFAULT_TEMPERATURE,
    ) -> None:
        self.model = model or self.default_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        api_key = self._require_api_key()
        self._client = AsyncOpenAI(api_key=api_key.get_secret_value())
        logger.info("OpenAIClient initialized (model=%s)", self.model)

    @staticmethod
    def _to_openai_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
        return [{"role": m.role.value, "content": m.content} for m in messages]

    def _request_kwargs(self, messages: list[ChatMessage], *, stream: bool = False) -> dict:
        kwargs: dict = {
            "model": self.model,
            "messages": self._to_openai_messages(messages),
            "max_tokens": self.max_tokens,
            "stream": stream,
        }
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        return kwargs

    @limit_concurrency(openai_sem)
    @timeout
    async def chat(self, messages: list[ChatMessage]) -> ModelResponse:
        logger.info("OpenAIClient.chat started (%d messages)", len(messages))
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=self._to_openai_messages(messages),
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            content = response.choices[0].message.content or ""
            logger.info("OpenAIClient.chat finished (%d chars)", len(content))
            return self._success_response(content)
        except OpenAIError as exc:
            # Catching specific errors like APITimeoutError / APIConnectionError / RateLimitError, we could trigger backoff and retry logic here.
            return self._error_response(exc)

    @limit_concurrency(openai_sem)
    @timeout
    async def chat_stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        logger.info("OpenAIClient.chat_stream started (%d messages)", len(messages))
        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=self._to_openai_messages(messages),
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            logger.info("OpenAIClient.chat_stream finished")
        except OpenAIError as exc:
            yield f"\n[⚠️ OpenAI Error: {exc}]"


class AnthropicClient(BaseLLMClient):
    default_model: str = "claude-haiku-4-5-20251001"
    provider: Provider = Provider.ANTHROPIC
    api_key_env: str = "ANTHROPIC_API_KEY"

    def __init__(
        self,
        model: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> None:
        self.model = model or self.default_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        api_key = self._require_api_key()
        self._client = AsyncAnthropic(api_key=api_key.get_secret_value())
        logger.info("AnthropicClient initialized (model=%s)", self.model)

    def _to_anthropic_payload(
        self, messages: list[ChatMessage]
    ) -> tuple[str | None, list[dict[str, str]]]:
        system = self._system_text(messages)
        conversation = [
            {"role": m.role.value, "content": m.content}
            for m in self._conversation(messages)
        ]
        return system, conversation

    @limit_concurrency(anthropic_sem)
    @timeout
    async def chat(self, messages: list[ChatMessage]) -> ModelResponse:
        logger.info("AnthropicClient.chat started (%d messages)", len(messages))
        system, conversation = self._to_anthropic_payload(messages)
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": conversation,
            "extra_body": {
                "temperature": self.temperature, # some models don't support temperature anymore
            },
        }
        if system:
            kwargs["system"] = system

        try:
            response = await self._client.messages.create(**kwargs)
            content = response.content[0].text if response.content else ""
            logger.info("AnthropicClient.chat finished (%d chars)", len(content))
            return self._success_response(content)
        except AnthropicError as exc:
            # Catching specific errors like APITimeoutError / APIConnectionError / RateLimitError, we could trigger backoff and retry logic here.
            return self._error_response(exc)


    @limit_concurrency(anthropic_sem)
    @timeout
    async def chat_stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        logger.info("AnthropicClient.chat_stream started (%d messages)", len(messages))
        system, conversation = self._to_anthropic_payload(messages)
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": conversation,
            "extra_body": {
                "temperature": self.temperature, # some models don't support temperature anymore
            },
        }
        if system:
            kwargs["system"] = system

        try:
            async with self._client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text
            logger.info("AnthropicClient.chat_stream finished")
        except AnthropicError as exc:
            yield f"\n[⚠️ Anthropic Error: {exc}]"


class GeminiClient(BaseLLMClient):
    default_model: str = "models/gemini-3.8-flash"
    provider: Provider = Provider.GEMINI
    api_key_env: str = "GEMINI_API_KEY"

    def __init__(
        self,
        model: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> None:
        self.model = model or self.default_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        api_key = self._require_api_key()
        self._client = genai.Client(api_key=api_key.get_secret_value())
        logger.info("GeminiClient initialized (model=%s)", self.model)

    def _to_gemini_history(
        self, messages: list[ChatMessage]
    ) -> tuple[str | None, list[dict], str]:
        """Split messages into system instruction, history, and the latest user turn."""
        system = self._system_text(messages)
        conversation = self._conversation(messages)
        if not conversation:
            raise ValueError("Gemini chat requires at least one non-system message.")

        *prior, latest = conversation
        history = [
            {
                "role": "user" if m.role is Role.USER else "model",
                "parts": [{"text": m.content}],
            }
            for m in prior
        ]
        return system, history, latest.content

    def _create_chat(self, messages: list[ChatMessage]):
        system, history, latest = self._to_gemini_history(messages)
        config: dict = {
            "max_output_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if system:
            config["system_instruction"] = system

        session = self._client.aio.chats.create(
            model=self.model,
            config=config,
            history=history,
        )
        return session, latest

    @limit_concurrency(gemini_sem)
    @timeout
    async def chat(self, messages: list[ChatMessage]) -> ModelResponse:
        logger.info("GeminiClient.chat started (%d messages)", len(messages))
        try:
            session, latest = self._create_chat(messages)
            response = await session.send_message(latest)
            content = response.text or ""
            logger.info("GeminiClient.chat finished (%d chars)", len(content))
            return self._success_response(content)
        except GeminiAPIError as exc:
            # Catching specific errors like APITimeoutError / APIConnectionError / RateLimitError, we could trigger backoff and retry logic here.
            return self._error_response(exc)

    @limit_concurrency(gemini_sem)
    @timeout
    async def chat_stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        logger.info("GeminiClient.chat_stream started (%d messages)", len(messages))
        try:
            session, latest = self._create_chat(messages)
            stream = await session.send_message_stream(latest)
            async for chunk in stream:
                text = chunk.text
                if text:
                    yield text
            logger.info("GeminiClient.chat_stream finished")
        except GeminiAPIError as exc:
            yield f"\n[⚠️ Gemini Error: {exc}]"
