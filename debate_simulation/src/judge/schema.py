"""Data schemas for the hostility judge (Model C).

The judge scores published messages on the same 0-4 scale the moderator uses,
but the two are independent measurements: the moderator scores a *candidate*
before publication, the judge scores what was *published*. In the treatment
condition those differ whenever the moderator intervened, and conflating them
in analysis would compare a message with its own replacement.

Each message is scored `RUNS_PER_MESSAGE` times so intra-judge consistency can
be measured (design doc §8.4). The runs are kept individually — the aggregate
is derived from them, never in place of them, per the metric-independence
principle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean, median
from typing import Annotated, Any

from pydantic import BaseModel, Field

from moderator.schema import HOSTILITY_MAX, HOSTILITY_MIN, Pathology, PublishedMessage

# Repeated evaluations per message, for intra-judge consistency.
RUNS_PER_MESSAGE = 3


@dataclass(frozen=True, slots=True)
class JudgementRequest:
    """One message to score, with the context it was replying to."""

    topic: str
    persona_id: str  # "persona_1" | "persona_2"
    turn: int
    message: str
    context: list[PublishedMessage] = field(default_factory=list)


class JudgementResponse(BaseModel):
    """Parsed JSON from one judge call.

    Deliberately NOT coupled: `targets_person` and `hostility_level`. The scale
    implies a message targeting the person scores at least 2, but forcing that
    would discard exactly the disagreements that reveal how the judge reasons.
    """

    hostility_level: Annotated[int, Field(ge=HOSTILITY_MIN, le=HOSTILITY_MAX)]
    pathologies_detected: list[Pathology] = Field(default_factory=list)
    justification: str
    targets_person: bool = False


@dataclass(slots=True)
class JudgementRun:
    """One of the repeated evaluations of a single message."""

    run_index: int  # 1-based
    response: JudgementResponse
    model_call: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JudgementRecord:
    """All runs for one message, plus the derived agreement summary."""

    experiment_id: str
    turn: int
    persona_id: str
    timestamp: str  # ISO 8601 with timezone
    topic: str
    condition: str
    message: str
    context_length: int
    runs: list[JudgementRun] = field(default_factory=list)

    @property
    def scores(self) -> list[int]:
        return [run.response.hostility_level for run in self.runs]

    @property
    def median_score(self) -> float | None:
        """The score to use in analysis: robust to a single outlying run."""
        return median(self.scores) if self.runs else None

    @property
    def mean_score(self) -> float | None:
        return mean(self.scores) if self.runs else None

    @property
    def score_range(self) -> int | None:
        """Spread across runs. 0 means the judge repeated itself exactly."""
        return max(self.scores) - min(self.scores) if self.runs else None

    @property
    def unanimous(self) -> bool:
        """Whether every run returned the same score."""
        return bool(self.runs) and self.score_range == 0

    def summary(self) -> dict[str, Any]:
        """Derived consistency figures, computed from the runs alone."""
        return {
            "runs": len(self.runs),
            "scores": self.scores,
            "median": self.median_score,
            "mean": self.mean_score,
            "range": self.score_range,
            "unanimous": self.unanimous,
        }