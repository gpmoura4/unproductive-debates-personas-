"""The debate loop — two personas alternating, with or without D5 moderation."""

from debate.loop import (
    CONTROL,
    SEATS,
    TREATMENT,
    DebateLoop,
    DebateResult,
    TurnResult,
    speaker_for_turn,
    write_transcript,
)

__all__ = [
    "CONTROL",
    "SEATS",
    "TREATMENT",
    "DebateLoop",
    "DebateResult",
    "TurnResult",
    "speaker_for_turn",
    "write_transcript",
]
