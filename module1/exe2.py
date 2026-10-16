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
from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel, SecretStr
# TODO: Importa los clientes asíncronos de openai y anthropic

class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class LLMConfig(BaseModel):
    """
    TODO: Define los campos para las API Keys usando SecretStr
    y una validación para asegurar que existan cuando se necesiten.
    """
    pass

class BaseLLMClient(ABC):
    @abstractmethod
    async def chat(self, prompt: str) -> str:
        pass

# TODO: Implementa OpenAIClient y AnthropicClient heredando de BaseLLMClient

class LLMFactory:
    @staticmethod
    def create_client(provider: Provider, config: LLMConfig) -> BaseLLMClient:
        # TODO: Implementa la lógica de selección de cliente
        pass

async def main():
    # TODO: Instancia la configuración y crea un cliente usando el Factory
    pass

if __name__ == "__main__":
    asyncio.run(main())
