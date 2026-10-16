"""
Abstracción de clientes y configuración robusta

Resumir
En la arquitectura de sistemas de IA, la capa de conexión es el cimiento de todo el flujo. Si esta capa es frágil, tu sistema sufrirá de tiempos de inactividad, fugas de secretos y dificultades para escalar o cambiar de proveedor.

¿Por qué abstraer los clientes?
Muchos desarrolladores cometen el error de instanciar clientes de OpenAI o Anthropic directamente en su lógica de negocio. Esto genera tres problemas graves:

Acoplamiento: Cambiar de GPT-4o a Claude 3.5 requiere reescribir docenas de líneas de código.
Dificultad de Testing: Es complejo simular (mockear) llamadas a la API si el cliente está "enterrado" en la lógica.
Inconsistencia: Cada SDK tiene firmas diferentes (choices[0].message vs content[0].text).
Patrón Factory y Validación con Pydantic
Para solucionar esto, utilizamos un Factory Pattern. Este patrón permite que el sistema decida qué cliente usar en tiempo de ejecución basándose en la configuración.

Además, en Python 3.12, la validación de tipos con Pydantic se vuelve obligatoria para manejar secretos de forma segura con SecretStr, evitando que tus llaves de API aparezcan accidentalmente en los logs de error.

Diferencias Clave que debes abstraer
OpenAI: Estructura de mensajes basada en role y content. Respuesta en choices.
Anthropic: Estructura similar pero con diferencias en la extracción del texto (content es una lista de objetos).
A continuación, implementaremos una base sólida que maneje estas diferencias de forma transparente para el resto de tu aplicación.
"""


import asyncio
import logging
import os
from abc import ABC, abstractmethod
from enum import Enum

from anthropic import AnthropicError, AsyncAnthropic
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, Field, SecretStr, ValidationError

logger = logging.getLogger(__name__)


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMConfig(BaseModel):
    """Non-secret client options. API keys are read inside each client."""

    model: str | None = None
    max_tokens: int = Field(default=256, gt=0)


class BaseLLMClient(ABC):
    @abstractmethod
    async def chat(self, prompt: str) -> str:
        pass


class OpenAIClient(BaseLLMClient):
    default_model = "gpt-4o-mini"
    api_key_env = "OPENAI_API_KEY"

    def __init__(self, model: str | None = None, max_tokens: int = 256) -> None:
        self.model = model or self.default_model
        self.max_tokens = max_tokens
        raw = os.environ.get(self.api_key_env, "").strip()
        if not raw:
            raise ValueError(
                f"{self.api_key_env} is not configured. "
                "Set it in the environment before using OpenAIClient."
            )
        api_key = SecretStr(raw)
        self._client = AsyncOpenAI(api_key=api_key.get_secret_value())

    async def chat(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content or ""


class AnthropicClient(BaseLLMClient):
    default_model = "claude-haiku-4-5-20251001"
    api_key_env = "ANTHROPIC_API_KEY"

    def __init__(self, model: str | None = None, max_tokens: int = 256) -> None:
        self.model = model or self.default_model
        self.max_tokens = max_tokens
        raw = os.environ.get(self.api_key_env, "").strip()
        if not raw:
            raise ValueError(
                f"{self.api_key_env} is not configured. "
                "Set it in the environment before using AnthropicClient."
            )
        api_key = SecretStr(raw)
        self._client = AsyncAnthropic(api_key=api_key.get_secret_value())

    async def chat(self, prompt: str) -> str:
        response = await self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text if response.content else ""


class LLMFactory:
    @staticmethod
    def create_client(provider: Provider, config: LLMConfig) -> BaseLLMClient:
        kwargs = {"model": config.model, "max_tokens": config.max_tokens}
        if provider is Provider.OPENAI:
            return OpenAIClient(**kwargs)
        if provider is Provider.ANTHROPIC:
            return AnthropicClient(**kwargs)
        raise ValueError(f"Unsupported provider: {provider!r}")


async def main():
    provider_raw = os.environ.get("PROVIDER", "openai").strip().lower()
    try:
        provider = Provider(provider_raw)
    except ValueError as exc:
        raise ValueError(
            f"Invalid PROVIDER={provider_raw!r}. Use 'openai' or 'anthropic'."
        ) from exc

    config = LLMConfig()
    client = LLMFactory.create_client(provider, config)

    prompt = "Say hello in one short sentence."
    try:
        logger.info("Calling %s.chat (model=%s)", type(client).__name__, client.model)
        answer = await client.chat(prompt)
    except ValidationError:
        logger.exception(
            "Validation error before/during chat for provider=%s model=%s",
            provider.value,
            client.model,
        )
        raise
    except (OpenAIError, AnthropicError):
        logger.exception(
            "SDK error from %s.chat (provider=%s model=%s prompt=%r)",
            type(client).__name__,
            provider.value,
            client.model,
            prompt,
        )
        raise

    print(f"{provider.value}: {answer}")



if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(main())
