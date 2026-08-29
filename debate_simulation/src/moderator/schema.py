"""Data schemas for the D5 Participatory Moderator.

The moderator evaluates each candidate debate message BEFORE publication and,
when hostility crosses the intervention threshold, returns a non-hostile
reformulation that preserves the argument.

Layering:
- `ModerationRequest` / `PublishedMessage` are plain dataclasses: they are
  built by us, from data we control.
- `ModerationResponse` is a pydantic model: it parses untrusted LLM output and
  is the only place where validation is enforced.
- `ModerationRecord` is the full log entry for one moderation call.

The response contract mirrors the OUTPUT FORMAT section of
`prompts/debate moderator D5/debate moderator D5.txt`, which is loaded
verbatim as the moderator system prompt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator

# Hostility scale bounds, per the HOSTILITY SCALE section of the prompt.
HOSTILITY_MIN = 0
HOSTILITY_MAX = 4

# Score at which the prompt instructs the moderator to intervene. Kept here as
# a named constant for the consistency check performed downstream (step 5) —
# it is deliberately NOT enforced by this module's validation. See
# `ModerationResponse` below.
INTERVENTION_THRESHOLD = 2


class Pathology(StrEnum):
    """Marc Angenot's three analytical categories of unproductive debate.

    These are the only values the moderator may report in
    `pathologies_detected`; the strings match the prompt's OUTPUT FORMAT
    exactly.
    """

    RHETORIC_OF_INCOMPREHENSION = "rhetoric_of_incomprehension"
    DISCURSIVE_INCOMMENSURABILITY = "discursive_incommensurability"
    ILLUSION_OF_RATIONALITY = "illusion_of_rationality"


@dataclass(frozen=True, slots=True)
class PublishedMessage:
    """A message that has already been published to the debate transcript.

    In the treatment condition this is the message as published — i.e. the
    reformulated text when the moderator intervened, not the original
    candidate.
    """

    turn: int
    persona_id: str  # "persona_1" | "persona_2"
    text: str


@dataclass(frozen=True, slots=True)
class ModerationRequest:
    """Everything the moderator needs to evaluate one candidate message."""

    topic: str
    persona_id: str  # "persona_1" | "persona_2"
    history: list[PublishedMessage] = field(default_factory=list)
    candidate: str = ""


class ModerationResponse(BaseModel):
    """Parsed JSON response from one moderator LLM call.

    Validation enforced here:
    - `hostility_level` within the 0-4 scale;
    - `pathologies_detected` restricted to the `Pathology` enum;
    - `requires_intervention` coupled to the presence of `reformulation`.

    Deliberately NOT enforced: agreement between `hostility_level` and
    `requires_intervention` (the prompt says level >= 2 means intervention).
    The model's `requires_intervention` is authoritative — a disagreement is
    real data about model behavior, so it is recorded downstream as
    `ModerationRecord.consistency_warning` rather than raised as an error
    that would discard the response.
    """

    hostility_level: Annotated[int, Field(ge=HOSTILITY_MIN, le=HOSTILITY_MAX)]
    pathologies_detected: list[Pathology]
    justification: str
    requires_intervention: bool
    reformulation: str | None = None
    argument_preserved: str | None = None

    @model_validator(mode="after")
    def _check_reformulation_matches_intervention(self) -> ModerationResponse:
        if self.requires_intervention:
            if self.reformulation is None or not self.reformulation.strip():
                raise ValueError(
                    "requires_intervention is true but reformulation is "
                    "missing or empty"
                )
        elif self.reformulation is not None:
            raise ValueError(
                "requires_intervention is false but a reformulation was "
                "provided"
            )
        return self

    def is_threshold_consistent(self) -> bool:
        """Whether the score and the intervention decision agree.

        False when the moderator scored at or above the threshold without
        intervening, or intervened below it. Callers record this as a warning;
        it is never treated as a validation failure.
        """
        return self.requires_intervention == (
            self.hostility_level >= INTERVENTION_THRESHOLD
        )


@dataclass(slots=True)
class ModerationRecord:
    """Full log entry for a single moderation call.

    One record per candidate message evaluated, whether or not the moderator
    intervened. Field set is provisional — finalized in step 5, together with
    the logger.
    """

    experiment_id: str
    turn: int
    persona_id: str
    timestamp: str  # ISO 8601 with timezone
    topic: str
    input: ModerationRequest
    moderation: ModerationResponse
    resolution: dict[str, Any] = field(default_factory=dict)
    model_call: dict[str, Any] = field(default_factory=dict)
    consistency_warning: str | None = None
