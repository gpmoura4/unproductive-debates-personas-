"""Metrics over a selected corpus of debates.

Everything here is arithmetic over what is already on disk — no model is
called, so the numbers are reproducible and free to recompute.

Three sources feed the metrics, and keeping them apart matters:

*   `judgements/` — the judge (model C) scoring what was **published**, three
    times per message, aggregated by median. This is the outcome measure.
*   `transcript.json` — per turn, whether the moderator saw the message
    (`moderated`) and whether it replaced it (`was_reformulated`).
*   `moderation/` — the moderator's own reading of the **candidate**: its
    hostility score, and its claim about what the reformulation preserved.

The moderator's score and the judge's score are never mixed into one figure.
They come from different models under different prompts, and one reads the
candidate while the other reads what replaced it; a difference between them
confounds the intervention's effect with disagreement between two raters.

Known confound, to be stated wherever the main effect is reported: from turn 2
onward the two conditions no longer share a history, because treatment
debaters reply to text the moderator has already softened. Part of any gap is
the direct effect of rewriting a message, part is indirect de-escalation. The
design cannot separate them, and that is a finding rather than a defect.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, pstdev

from analysis.selection import Replicate, Run, Selection

HOSTILITY_MIN = 0
HOSTILITY_MAX = 4


@dataclass(frozen=True, slots=True)
class TurnRecord:
    """One published message: what the judge gave it, and how it got there."""

    turn: int
    persona_id: str
    condition: str
    score: int | None          # judge median over its runs
    scores: list[int]          # the individual judge runs
    unanimous: bool | None
    moderated: bool            # the moderator saw this candidate
    reformulated: bool         # ... and replaced it
    moderator_score: int | None  # the moderator's read of the candidate
    argument_preserved: str | None
    consistency_warning: str | None


@dataclass(frozen=True, slots=True)
class DebateRecord:
    """One debate — a single condition of a single replicate."""

    topic: str
    pair_id: str
    replicate: int
    condition: str
    experiment_id: str
    turns: list[TurnRecord]

    @property
    def mean_hostility(self) -> float | None:
        scores = [t.score for t in self.turns if t.score is not None]
        return mean(scores) if scores else None


@dataclass(frozen=True, slots=True)
class CellRecord:
    """One replicate: the control and treatment debates that pair up."""

    topic: str
    pair_id: str
    replicate: int
    control: DebateRecord
    treatment: DebateRecord

    @property
    def delta(self) -> float | None:
        """Treatment minus control. Negative means the moderator lowered it."""
        if self.control.mean_hostility is None:
            return None
        if self.treatment.mean_hostility is None:
            return None
        return self.treatment.mean_hostility - self.control.mean_hostility


def _load_judgements(run: Run) -> dict[int, dict]:
    """Judge summaries by turn number."""
    out: dict[int, dict] = {}
    judgements = run.path / "judgements"
    if not judgements.is_dir():
        return out
    for path in sorted(judgements.glob("turn_*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        turn = record.get("turn")
        if turn is not None:
            out[turn] = record
    return out


def _load_moderation(run: Run) -> dict[int, dict]:
    """Moderation records by turn number. Empty in the control condition."""
    out: dict[int, dict] = {}
    moderation = run.path / "moderation"
    if not moderation.is_dir():
        return out
    for path in sorted(moderation.glob("turn_*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        turn = record.get("turn")
        if turn is not None:
            out[turn] = record
    return out


def load_debate(run: Run) -> DebateRecord:
    """Join transcript, judgements and moderation into per-turn records."""
    transcript = json.loads((run.path / "transcript.json").read_text(encoding="utf-8"))
    judgements = _load_judgements(run)
    moderation = _load_moderation(run)

    turns: list[TurnRecord] = []
    for entry in transcript.get("turns", []):
        turn = entry.get("turn")
        judgement = judgements.get(turn, {})
        summary = judgement.get("summary", {})
        record = moderation.get(turn, {})
        moderation_block = record.get("moderation", {})

        turns.append(
            TurnRecord(
                turn=turn,
                persona_id=entry.get("persona_id", ""),
                condition=run.condition,
                score=summary.get("median"),
                scores=list(summary.get("scores", [])),
                unanimous=summary.get("unanimous"),
                moderated=bool(entry.get("moderated")),
                reformulated=bool(entry.get("was_reformulated")),
                moderator_score=moderation_block.get("hostility_level"),
                argument_preserved=moderation_block.get("argument_preserved"),
                consistency_warning=record.get("consistency_warning"),
            )
        )

    return DebateRecord(
        topic=run.topic,
        pair_id=run.pair_id,
        replicate=0,
        condition=run.condition,
        experiment_id=run.experiment_id,
        turns=turns,
    )


def load_cells(selection: Selection) -> list[CellRecord]:
    """Every replicate in the selection, with both conditions loaded."""
    cells: list[CellRecord] = []
    for replicate in selection.replicates:
        control = load_debate(replicate.control)
        treatment = load_debate(replicate.treatment)
        cells.append(
            CellRecord(
                topic=replicate.topic,
                pair_id=replicate.pair_id,
                replicate=replicate.index,
                control=DebateRecord(
                    control.topic, control.pair_id, replicate.index,
                    control.condition, control.experiment_id, control.turns,
                ),
                treatment=DebateRecord(
                    treatment.topic, treatment.pair_id, replicate.index,
                    treatment.condition, treatment.experiment_id, treatment.turns,
                ),
            )
        )
    return cells


def _summarise(values: list[float]) -> dict:
    """Mean, spread and n. Population sd: these are all the cells there are."""
    if not values:
        return {"n": 0, "mean": None, "sd": None, "min": None, "max": None}
    return {
        "n": len(values),
        "mean": round(mean(values), 4),
        "sd": round(pstdev(values), 4) if len(values) > 1 else 0.0,
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def main_effect(cells: list[CellRecord]) -> dict:
    """Metric 1 — mean hostility under each condition, and the gap.

    Aggregated over cells rather than over messages, so a debate where the
    judge scored more turns cannot outweigh the others. The paired delta is
    reported alongside: because control and treatment share a persona pair and
    topic, the within-cell difference removes between-cell variation that the
    two condition means still carry.
    """
    control = [c.control.mean_hostility for c in cells if c.control.mean_hostility is not None]
    treatment = [c.treatment.mean_hostility for c in cells if c.treatment.mean_hostility is not None]
    deltas = [c.delta for c in cells if c.delta is not None]

    return {
        "control": _summarise(control),
        "treatment": _summarise(treatment),
        "delta": _summarise(deltas),
        "cells_favouring_treatment": sum(1 for d in deltas if d < 0),
        "cells_favouring_control": sum(1 for d in deltas if d > 0),
        "cells_tied": sum(1 for d in deltas if d == 0),
    }


def main_effect_by_topic(cells: list[CellRecord]) -> dict[str, dict]:
    topics = sorted({c.topic for c in cells})
    return {
        topic: main_effect([c for c in cells if c.topic == topic])
        for topic in topics
    }


def per_turn_trajectory(cells: list[CellRecord]) -> dict[str, dict[int, dict]]:
    """Mean hostility at each turn index, per condition.

    This is where escalation shows up, and where the history confound is
    visible: the two lines start from comparable ground at turn 1 and diverge
    as the treatment history accumulates rewritten text.
    """
    out: dict[str, dict[int, dict]] = {"control": {}, "treatment": {}}
    for condition in ("control", "treatment"):
        by_turn: dict[int, list[float]] = {}
        for cell in cells:
            debate = getattr(cell, condition)
            for turn in debate.turns:
                if turn.score is not None:
                    by_turn.setdefault(turn.turn, []).append(turn.score)
        out[condition] = {
            turn: _summarise(scores) for turn, scores in sorted(by_turn.items())
        }
    return out


def activation(cells: list[CellRecord]) -> dict:
    """Metric 2 — how often D5 fired, and how often it rewrote.

    `off_threshold` counts turns where the moderator's own decision disagreed
    with its own score (intervening below the threshold, or declining at or
    above it). It is logged by the moderator itself, so it measures calibration
    without a second rater.
    """
    total = flagged = reformulated = 0
    off_threshold = 0
    warnings: Counter[str] = Counter()

    for cell in cells:
        for turn in cell.treatment.turns:
            total += 1
            if turn.moderated:
                flagged += 1
            if turn.reformulated:
                reformulated += 1
            if turn.consistency_warning:
                off_threshold += 1
                kind = (
                    "intervened_below_threshold"
                    if turn.consistency_warning.startswith("Intervened")
                    else "declined_at_or_above_threshold"
                )
                warnings[kind] += 1

    def _rate(part: int) -> float | None:
        return round(part / total, 4) if total else None

    return {
        "treatment_turns": total,
        "moderated": flagged,
        "moderated_rate": _rate(flagged),
        "reformulated": reformulated,
        "reformulated_rate": _rate(reformulated),
        "reformulated_rate_of_moderated": (
            round(reformulated / flagged, 4) if flagged else None
        ),
        "off_threshold_decisions": off_threshold,
        "off_threshold_rate": _rate(off_threshold),
        "off_threshold_breakdown": dict(warnings),
    }


def judge_consistency(cells: list[CellRecord]) -> dict:
    """Metric 3 — intra-judge agreement across the three runs per message.

    Inter-judge agreement (models A and B rating the same messages) is not
    computed here: no such ratings exist on disk. See docs/metrics_pending.md.
    """
    total = unanimous = 0
    ranges: Counter[int] = Counter()
    distribution: Counter[int] = Counter()

    for cell in cells:
        for debate in (cell.control, cell.treatment):
            for turn in debate.turns:
                if turn.score is None:
                    continue
                total += 1
                if turn.unanimous:
                    unanimous += 1
                if turn.scores:
                    ranges[max(turn.scores) - min(turn.scores)] += 1
                distribution[turn.score] += 1

    return {
        "messages_scored": total,
        "unanimous": unanimous,
        "unanimous_rate": round(unanimous / total, 4) if total else None,
        "range_distribution": {str(k): v for k, v in sorted(ranges.items())},
        "score_distribution": {
            str(level): distribution.get(level, 0)
            for level in range(HOSTILITY_MIN, HOSTILITY_MAX + 1)
        },
    }


def score_distribution_by_condition(cells: list[CellRecord]) -> dict[str, dict[str, int]]:
    """Judge scores 0-4 under each condition, for the distribution plot."""
    out: dict[str, dict[str, int]] = {}
    for condition in ("control", "treatment"):
        counter: Counter[int] = Counter()
        for cell in cells:
            for turn in getattr(cell, condition).turns:
                if turn.score is not None:
                    counter[turn.score] += 1
        out[condition] = {
            str(level): counter.get(level, 0)
            for level in range(HOSTILITY_MIN, HOSTILITY_MAX + 1)
        }
    return out


def argument_preservation(cells: list[CellRecord]) -> dict:
    """Metric 4 — the moderator's own claim that it kept the position.

    IMPORTANT: this is self-reported. The moderator writes `argument_preserved`
    in the same call that produces the reformulation, so a high rate means the
    field was filled in, not that the stance survived. Piloting found cases
    where the moderator declared preservation while carrying the attack
    through. Report it as declared coverage; verified preservation needs an
    independent rater (docs/metrics_pending.md).
    """
    reformulated = declared = 0
    lengths: list[int] = []

    for cell in cells:
        for turn in cell.treatment.turns:
            if not turn.reformulated:
                continue
            reformulated += 1
            claim = (turn.argument_preserved or "").strip()
            if claim:
                declared += 1
                lengths.append(len(claim))

    return {
        "reformulations": reformulated,
        "preservation_declared": declared,
        "declared_rate": (
            round(declared / reformulated, 4) if reformulated else None
        ),
        "mean_claim_length_chars": round(mean(lengths), 1) if lengths else None,
        "self_reported": True,
    }


def per_cell_table(cells: list[CellRecord]) -> list[dict]:
    """One row per replicate — the basis for the per-cell delta plot."""
    rows = []
    for cell in cells:
        rows.append(
            {
                "topic": cell.topic,
                "pair_id": cell.pair_id,
                "replicate": cell.replicate,
                "control_mean": (
                    round(cell.control.mean_hostility, 4)
                    if cell.control.mean_hostility is not None else None
                ),
                "treatment_mean": (
                    round(cell.treatment.mean_hostility, 4)
                    if cell.treatment.mean_hostility is not None else None
                ),
                "delta": round(cell.delta, 4) if cell.delta is not None else None,
                "control_id": cell.control.experiment_id,
                "treatment_id": cell.treatment.experiment_id,
            }
        )
    return sorted(rows, key=lambda r: (r["topic"], r["pair_id"], r["replicate"]))


def per_turn_table(cells: list[CellRecord]) -> list[dict]:
    """One row per published message — the long-format export."""
    rows = []
    for cell in cells:
        for condition in ("control", "treatment"):
            debate = getattr(cell, condition)
            for turn in debate.turns:
                rows.append(
                    {
                        "topic": cell.topic,
                        "pair_id": cell.pair_id,
                        "replicate": cell.replicate,
                        "condition": condition,
                        "turn": turn.turn,
                        "persona_id": turn.persona_id,
                        "judge_score": turn.score,
                        "judge_runs": "|".join(str(s) for s in turn.scores),
                        "unanimous": turn.unanimous,
                        "moderated": turn.moderated,
                        "reformulated": turn.reformulated,
                        "moderator_score": turn.moderator_score,
                        "off_threshold": bool(turn.consistency_warning),
                    }
                )
    return rows


def compute_all(selection: Selection) -> dict:
    """Every metric that the corpus on disk can support."""
    cells = load_cells(selection)
    return {
        "corpus": {
            "balanced": selection.balanced,
            "topics": sorted({c.topic for c in cells}),
            "cells": len({(c.topic, c.pair_id) for c in cells}),
            "replicates": len(cells),
            "debates": len(cells) * 2,
            "turns_per_debate": selection.expected_turns,
            "excluded_runs": len(selection.excluded),
        },
        "main_effect": main_effect(cells),
        "main_effect_by_topic": main_effect_by_topic(cells),
        "per_turn": per_turn_trajectory(cells),
        "activation": activation(cells),
        "judge_consistency": judge_consistency(cells),
        "score_distribution": score_distribution_by_condition(cells),
        "argument_preservation": argument_preservation(cells),
        "per_cell": per_cell_table(cells),
    }
