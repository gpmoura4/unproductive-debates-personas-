"""One debating agent: a persona plus the shared behavioral layer.

Simpler than the moderator by design — the output is free text, so there is no
JSON contract to parse. What can still go wrong is an empty reply or a model
that wraps the message in quotes or a name prefix, which `generate_turn`
normalizes before the text enters the transcript.
"""

from __future__ import annotations

from llm.client import LLMClient
from moderator.schema import PublishedMessage

from debater.prompt import (
    build_system_prompt,
    build_user_message,
    load_behavior_prompt,
    load_persona_prompt,
    prompt_sha256,
)

# Prefixes a model may add despite the instruction not to; stripped so the
# transcript holds the message itself.
_SPEAKER_PREFIXES = ("YOU:", "OPPONENT:", "Persona 1:", "Persona 2:", "Me:")


class DebaterError(RuntimeError):
    """Raised when a debater cannot produce a usable message."""


def _strip_speaker_prefix(text: str) -> str:
    for prefix in _SPEAKER_PREFIXES:
        if text.lower().startswith(prefix.lower()):
            return text[len(prefix) :].lstrip()
    return text


def _strip_wrapping_quotes(text: str) -> str:
    """Remove quotes wrapping the whole message, keeping internal ones."""
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        inner = text[1:-1]
        if text[0] not in inner:
            return inner.strip()
    return text


def clean_message(raw_text: str) -> str:
    """Normalize a raw model reply into a publishable message.

    Raises `DebaterError` on an empty result rather than publishing a blank
    turn, which would silently corrupt the transcript.
    """
    text = _strip_wrapping_quotes(_strip_speaker_prefix(raw_text.strip()))
    if not text:
        raise DebaterError("Debater returned an empty message.")
    return text


class Debater:
    """A persona debating under the shared behavioral rules.

    The system prompt is composed once at construction: it depends on the
    persona, the behavioral layer and the topic, none of which change during a
    debate. Only the history varies per turn.
    """

    def __init__(
        self,
        client: LLMClient,
        persona_id: str,
        topic: str,
        pole: str | None = None,
        persona_index: int | None = None,
        persona_prompt: str | None = None,
        behavior_prompt: str | None = None,
    ) -> None:
        if persona_prompt is None:
            if pole is None or persona_index is None:
                raise ValueError(
                    "Provide either persona_prompt, or both pole and "
                    "persona_index to load it from disk."
                )
            persona_prompt = load_persona_prompt(pole, persona_index)

        if behavior_prompt is None:
            behavior_prompt = load_behavior_prompt()

        self.client = client
        self.persona_id = persona_id
        self.topic = topic
        self.pole = pole
        self.persona_index = persona_index
        self.system_prompt = build_system_prompt(
            persona_prompt, behavior_prompt, topic
        )
        self.system_prompt_sha256 = prompt_sha256(self.system_prompt)

    def generate_turn(
        self, history: list[PublishedMessage]
    ) -> tuple[str, dict]:
        """Produce this persona's next message.

        `history` is the published transcript so far — the reformulated text
        where the moderator intervened. Returns the cleaned message and the
        call metadata for the log.
        """
        user_message = build_user_message(history, self.persona_id)
        raw_text, call_metadata = self.client.call(
            self.system_prompt, user_message
        )

        metadata = {
            **call_metadata,
            "system_prompt_sha256": self.system_prompt_sha256,
            "raw_text": raw_text,
        }
        return clean_message(raw_text), metadata
