"""LLM transport shared by all three experiment roles.

OpenRouter and Ollama both expose OpenAI-compatible chat endpoints, so a
single adapter serves both: the difference is the `base_url`, whether an API
key is required, and which extra headers are sent.

`LLMClient.call()` returns the raw text plus call metadata (latency, usage,
attempts) for the experiment log. Parsing that text — into a moderation
verdict, a judge score, a debate turn — belongs to the caller.
"""

from __future__ import annotations

import os
import random
import time
from typing import Any

import openai
from openai import OpenAI

from config.loader import ModelConfig

# Retries apply only to transient failures; auth errors and malformed
# requests fail immediately, since retrying cannot help.
MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_MAX_SECONDS = 30.0

REQUEST_TIMEOUT_SECONDS = 120.0

# Ollama ignores the key but the OpenAI SDK requires a non-empty string.
OLLAMA_PLACEHOLDER_KEY = "ollama"

# Optional, recommended by OpenRouter for their rankings/analytics.
OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://github.com/gpcmoura/unproductive-debates-personas",
    "X-Title": "debate-simulation-cscw",
}


class LLMCallError(RuntimeError):
    """Raised when a call fails and cannot (or should not) be retried."""


def _reasoning_token_count(response: Any) -> int | None:
    """Reasoning tokens reported by the provider, when it reports them."""
    usage = getattr(response, "usage", None)
    details = getattr(usage, "completion_tokens_details", None)
    return getattr(details, "reasoning_tokens", None)


def _is_transient(exc: Exception) -> bool:
    """Whether an exception is worth retrying.

    Transient: rate limits (429), timeouts, connection failures, 5xx.
    Not transient: auth (401/403), bad request (400), not found (404) — the
    same call would fail the same way.
    """
    if isinstance(exc, (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError)):
        return True
    if isinstance(exc, openai.APIStatusError):
        return exc.status_code >= 500
    return False


def _backoff_seconds(attempt: int) -> float:
    """Exponential backoff with jitter, to avoid synchronized retries."""
    delay = min(BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)), BACKOFF_MAX_SECONDS)
    return delay * (0.5 + random.random() / 2)


class OpenAICompatibleAdapter:
    """Wraps the OpenAI SDK for both OpenRouter and Ollama."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self._client = OpenAI(
            base_url=self._resolve_base_url(config),
            api_key=self._resolve_api_key(config),
            default_headers=self._resolve_headers(config),
            timeout=REQUEST_TIMEOUT_SECONDS,
            max_retries=0,  # retries are handled here, so attempts are counted
        )

    @staticmethod
    def _resolve_base_url(config: ModelConfig) -> str:
        """Normalize to the OpenAI-compatible endpoint.

        Ollama serves it at /v1, but the config lists the server root
        (http://localhost:11434), so append it when absent.
        """
        base = config.base_url.rstrip("/")
        if config.provider == "ollama" and not base.endswith("/v1"):
            base = f"{base}/v1"
        return base

    @staticmethod
    def _resolve_api_key(config: ModelConfig) -> str:
        if not config.api_key_env:
            # Ollama accepts any string; a real provider without a configured
            # env var would have been rejected by the config loader.
            return OLLAMA_PLACEHOLDER_KEY

        key = os.environ.get(config.api_key_env)
        if not key:
            raise LLMCallError(
                f"Role '{config.role}': environment variable "
                f"{config.api_key_env} is not set."
            )
        return key

    @staticmethod
    def _resolve_headers(config: ModelConfig) -> dict[str, str] | None:
        if config.provider == "openrouter":
            return dict(OPENROUTER_HEADERS)
        return None

    def complete(self, system_prompt: str, user_message: str) -> Any:
        return self._client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )


class LLMClient:
    """One configured model, callable for a single system+user exchange."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self._adapter = OpenAICompatibleAdapter(config)

    def call(self, system_prompt: str, user_message: str) -> tuple[str, dict]:
        """Send one completion request.

        Returns `(raw_text, metadata)`, where metadata carries model, provider,
        temperature, latency_ms, usage and attempts. `usage` is None when the
        provider does not report token counts (Ollama often does not) — counts
        are never fabricated.

        Retries transient failures up to MAX_ATTEMPTS with exponential backoff.
        Raises `LLMCallError` when all attempts fail or the error is not
        retryable.
        """
        started = time.monotonic()
        last_exc: Exception | None = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = self._adapter.complete(system_prompt, user_message)
            except Exception as exc:  # noqa: BLE001 — re-raised as LLMCallError below
                last_exc = exc
                if not _is_transient(exc) or attempt == MAX_ATTEMPTS:
                    break
                time.sleep(_backoff_seconds(attempt))
                continue

            latency_ms = int((time.monotonic() - started) * 1000)
            return self._extract_text(response), {
                "model": self.config.model,
                "provider": self.config.provider,
                "temperature": self.config.temperature,
                "latency_ms": latency_ms,
                "usage": self._extract_usage(response),
                "attempts": attempt,
            }

        raise LLMCallError(
            f"Role '{self.config.role}' ({self.config.provider}/"
            f"{self.config.model}) failed after {attempt} attempt(s): "
            f"{type(last_exc).__name__}: {last_exc}"
        ) from last_exc

    @staticmethod
    def _extract_text(response: Any) -> str:
        choices = getattr(response, "choices", None)
        if not choices:
            raise LLMCallError(f"Response contained no choices: {response!r}")

        choice = choices[0]
        content = choice.message.content
        if content is None:
            # The usual cause is a reasoning model whose thinking tokens
            # exhaust max_tokens before any content is emitted, which the API
            # reports as finish_reason="length" with a null message. Say so:
            # the fix is a larger max_tokens for that role, not a retry.
            finish_reason = getattr(choice, "finish_reason", None)
            hint = ""
            if finish_reason == "length":
                reasoning = _reasoning_token_count(response)
                hint = (
                    " The response was truncated by max_tokens"
                    + (f" after {reasoning} reasoning tokens" if reasoning else "")
                    + "; raise max_tokens for this role in config/models.yaml."
                )
            raise LLMCallError(
                f"Response message had no content "
                f"(finish_reason={finish_reason!r}).{hint}"
            )
        return content

    @staticmethod
    def _extract_usage(response: Any) -> dict[str, int] | None:
        """Token counts when the provider reports them, else None."""
        usage = getattr(response, "usage", None)
        if usage is None:
            return None

        fields = ("prompt_tokens", "completion_tokens", "total_tokens")
        extracted = {f: getattr(usage, f, None) for f in fields}
        if all(v is None for v in extracted.values()):
            return None
        return {k: v for k, v in extracted.items() if v is not None}
