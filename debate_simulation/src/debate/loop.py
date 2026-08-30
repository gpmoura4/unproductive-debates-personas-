"""The debate loop: two personas alternating, optionally moderated.

Per turn:

    debater proposes a candidate
      -> treatment: the D5 moderator scores it and may reformulate
      -> control:   the candidate is published unchanged
    -> the published text is appended to the transcript
    -> the other persona replies to what was published

That last step is what propagates the D5 effect: the opponent answers the
message that was allowed through, not the one that was attempted.

Moderation failure is not fatal. When the moderator cannot produce a usable
verdict after its retry, the candidate is published and the turn is marked
`moderated: false`. A treatment debate can therefore contain unmoderated
turns, which is why every turn records whether it was moderated — averaging
hostility over a treatment run without excluding them would understate the
intervention's effect.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from debater.debater import Debater
from moderator.moderator import D5Moderator, ModerationParseError
from moderator.schema import ModerationRequest, PublishedMessage

CONTROL = "control"
TREATMENT = "treatment"

# Seat order: persona_1 opens, then they alternate.
SEATS = ("persona_1", "persona_2")


@dataclass(slots=True)
class TurnResult:
    """One completed turn, as it enters the transcript."""

    turn: int
    persona_id: str
    candidate: str
    published_text: str
    was_reformulated: bool
    moderated: bool
    hostility_level: int | None = None
    pathologies_detected: list[str] = field(default_factory=list)
    consistency_warning: str | None = None
    moderation_error: str | None = None

    def to_published_message(self) -> PublishedMessage:
        return PublishedMessage(
            turn=self.turn, persona_id=self.persona_id, text=self.published_text
        )


@dataclass(slots=True)
class DebateResult:
    """A finished (or partial) debate."""

    experiment_id: str
    topic: str
    condition: str
    turns: list[TurnResult]
    completed: bool
    stopped_reason: str | None = None

    @property
    def transcript(self) -> list[PublishedMessage]:
        return [t.to_published_message() for t in self.turns]

    @property
    def unmoderated_turns(self) -> list[int]:
        """Turns published without a verdict — treatment condition only."""
        return [t.turn for t in self.turns if not t.moderated]

    @property
    def intervention_count(self) -> int:
        return sum(1 for t in self.turns if t.was_reformulated)


def speaker_for_turn(turn: int) -> str:
    """persona_1 on odd turns, persona_2 on even ones."""
    return SEATS[(turn - 1) % len(SEATS)]


class DebateLoop:
    """Runs one debate between two personas under one condition."""

    def __init__(
        self,
        experiment_id: str,
        topic: str,
        condition: str,
        debaters: dict[str, Debater],
        moderator: D5Moderator | None = None,
        logger: Any = None,
    ) -> None:
        if condition not in (CONTROL, TREATMENT):
            raise ValueError(
                f"Unknown condition {condition!r}; expected {CONTROL!r} or "
                f"{TREATMENT!r}."
            )
        if condition == TREATMENT and moderator is None:
            raise ValueError("The treatment condition requires a moderator.")
        missing = set(SEATS) - set(debaters)
        if missing:
            raise ValueError(f"Missing debaters for: {sorted(missing)}")

        self.experiment_id = experiment_id
        self.topic = topic
        self.condition = condition
        self.debaters = debaters
        self.moderator = moderator
        self.logger = logger

    def run(
        self,
        planned_turns: int,
        history: list[PublishedMessage] | None = None,
        on_turn: Any = None,
    ) -> DebateResult:
        """Run turns until `planned_turns`, resuming from `history` if given.

        `on_turn` is called with each `TurnResult` as it completes, for live
        progress output. A debater failure stops the debate and returns what
        was produced so far — partial results are kept, never discarded.
        """
        transcript = list(history or [])
        turns: list[TurnResult] = []
        start_turn = len(transcript) + 1

        for turn in range(start_turn, planned_turns + 1):
            speaker = speaker_for_turn(turn)
            try:
                result = self._run_turn(turn, speaker, transcript)
            except Exception as exc:  # noqa: BLE001 — partial results are kept
                # KeyboardInterrupt and SystemExit derive from BaseException,
                # so they propagate rather than being swallowed here.
                return DebateResult(
                    experiment_id=self.experiment_id,
                    topic=self.topic,
                    condition=self.condition,
                    turns=turns,
                    completed=False,
                    stopped_reason=f"{type(exc).__name__}: {exc}",
                )

            turns.append(result)
            transcript.append(result.to_published_message())
            if on_turn is not None:
                on_turn(result)

        return DebateResult(
            experiment_id=self.experiment_id,
            topic=self.topic,
            condition=self.condition,
            turns=turns,
            completed=True,
        )

    def _run_turn(
        self, turn: int, speaker: str, transcript: list[PublishedMessage]
    ) -> TurnResult:
        candidate, _ = self.debaters[speaker].generate_turn(transcript)

        if self.condition == CONTROL:
            return TurnResult(
                turn=turn,
                persona_id=speaker,
                candidate=candidate,
                published_text=candidate,
                was_reformulated=False,
                moderated=False,
            )

        return self._moderate_turn(turn, speaker, transcript, candidate)

    def _moderate_turn(
        self,
        turn: int,
        speaker: str,
        transcript: list[PublishedMessage],
        candidate: str,
    ) -> TurnResult:
        """Score and possibly reformulate one candidate.

        On an irrecoverable moderation failure the candidate is published as-is
        and the turn is marked unmoderated: losing the rest of the debate to one
        bad reply would cost more than the turn is worth. The failure itself is
        already logged by the moderator.
        """
        request = ModerationRequest(
            topic=self.topic,
            persona_id=speaker,
            history=list(transcript),
            candidate=candidate,
        )

        try:
            response = self.moderator.moderate(
                request, experiment_id=self.experiment_id, turn=turn
            )
        except ModerationParseError as exc:
            return TurnResult(
                turn=turn,
                persona_id=speaker,
                candidate=candidate,
                published_text=candidate,
                was_reformulated=False,
                moderated=False,
                moderation_error=f"{type(exc).__name__}: {exc}",
            )

        published = self.moderator.resolve_published_text(request, response)
        return TurnResult(
            turn=turn,
            persona_id=speaker,
            candidate=candidate,
            published_text=published,
            was_reformulated=response.requires_intervention,
            moderated=True,
            hostility_level=response.hostility_level,
            pathologies_detected=[p.value for p in response.pathologies_detected],
            consistency_warning=self.moderator.consistency_warning(response),
        )


def write_transcript(result: DebateResult, experiment_dir: Path) -> Path:
    """Persist the debate transcript beside the moderation records.

    Written separately rather than derived from the moderation log because the
    control condition produces no moderation records at all — the transcript
    has to work identically in both conditions.
    """
    experiment_dir = Path(experiment_dir)
    experiment_dir.mkdir(parents=True, exist_ok=True)
    path = experiment_dir / "transcript.json"

    payload = {
        "experiment_id": result.experiment_id,
        "topic": result.topic,
        "condition": result.condition,
        "written_at": datetime.now().astimezone().isoformat(),
        "completed": result.completed,
        "stopped_reason": result.stopped_reason,
        "turn_count": len(result.turns),
        "intervention_count": result.intervention_count,
        "unmoderated_turns": result.unmoderated_turns,
        "turns": [asdict(t) for t in result.turns],
    }
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return path
