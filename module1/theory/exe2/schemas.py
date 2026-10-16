from enum import Enum

from pydantic import BaseModel, Field, field_validator

DEFAULT_MAX_TOKENS = 256
DEFAULT_TEMPERATURE = 0.7


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    content: str
    role: Role

    @field_validator("role")
    @classmethod
    def role_valid(cls, v: str) -> str:
        roles_allowed = {Role.USER.value, Role.ASSISTANT.value, Role.SYSTEM.value}
        if v not in roles_allowed:
            raise ValueError(f"Role must be one of {roles_allowed}, received: '{v}'")
        return v

class ModelResponse(BaseModel):
    provider: Provider
    model: str
    content: str | None = None
    error: str | None = None


class LLMConfig(BaseModel):
    provider: Provider
    model: str | None = None
    max_tokens: int = Field(default=DEFAULT_MAX_TOKENS, gt=0)
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=2.0)
