"""LLM transport shared by the debater, moderator and judge roles."""

from llm.client import (
    MAX_ATTEMPTS,
    LLMCallError,
    LLMClient,
    OpenAICompatibleAdapter,
)

__all__ = [
    "MAX_ATTEMPTS",
    "LLMCallError",
    "LLMClient",
    "OpenAICompatibleAdapter",
]
