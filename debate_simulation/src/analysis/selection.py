"""Which runs belong in the analysis, and why the others do not.

`experiments/` accumulates everything ever run: smoke tests, pilots on older
prompts, runs cut short by a timeout. Analysis needs a defensible subset, and
"defensible" here means a reader can re-derive the same subset from the
manifests without taking our word for it.

Three filters, applied in order:

1.  **Eligibility** — a run must be complete on its own terms: the planned
    number of turns, all of them actually taken, and one judgement file per
    turn. A truncated debate is not a short debate; its hostility trajectory
    was interrupted mid-escalation.

2.  **Prompt identity** — the manifest records a sha256 for each prompt. Runs
    are grouped by the (behavior, judge, moderator) triple, and only the
    cohort sharing the dominant triple is kept. This is what makes the corpus
    homogeneous: filtering by timestamp would only approximate it.

3.  **Conditional pairing** — control and treatment of the same cell survive
    together or not at all. The comparison is within-cell, so a control whose
    treatment was dropped contributes nothing and would silently unbalance the
    means.

A *cell* is one (topic, pair) combination. A *replicate* is one full
control+treatment pass over a cell; the overnight batch was launched twice, so
most cells have two. Replicates are matched by chronological order within the
cell, which is arbitrary but consistent — and harmless, because generation is
stochastic (the manifest's `seed` field is recorded but never reaches the
model), so replicates are interchangeable.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Exclusion(str, Enum):
    """Why a run was left out. Every dropped run carries one of these."""

    NO_MANIFEST = "no_manifest"
    NO_TRANSCRIPT = "no_transcript"
    INCOMPLETE = "incomplete"
    TURN_COUNT_MISMATCH = "turn_count_mismatch"
    UNEXPECTED_TURNS = "unexpected_turns"
    MISSING_JUDGEMENTS = "missing_judgements"
    PROMPT_MISMATCH = "prompt_mismatch"
    UNPAIRED_CONDITION = "unpaired_condition"
    SURPLUS_REPLICATE = "surplus_replicate"
    SURPLUS_CELL = "surplus_cell"


@dataclass(frozen=True, slots=True)
class PromptTriple:
    """The prompt versions a run was produced under.

    `moderator` is None in the control condition, which runs without one. That
    asymmetry is why cohort matching compares control and treatment runs on
    their own terms rather than requiring an identical triple across both.
    """

    behavior: str | None
    judge: str | None
    moderator: str | None


@dataclass(frozen=True, slots=True)
class Run:
    """One debate directory, parsed enough to decide whether it qualifies."""

    path: Path
    experiment_id: str
    topic: str
    pair_id: str
    condition: str  # "control" | "treatment"
    planned_turns: int
    turn_count: int | None
    completed: bool
    judgement_count: int
    prompts: PromptTriple
    created_at: str

    @property
    def cell(self) -> tuple[str, str]:
        return (self.topic, self.pair_id)


@dataclass(frozen=True, slots=True)
class Excluded:
    """A run that did not make the cut, with the reason and its details."""

    experiment_id: str
    topic: str | None
    pair_id: str | None
    condition: str | None
    reason: Exclusion
    detail: str


@dataclass(frozen=True, slots=True)
class Replicate:
    """One control+treatment pass over a cell — the unit of comparison."""

    topic: str
    pair_id: str
    index: int  # 1-based, chronological within the cell
    control: Run
    treatment: Run


@dataclass(frozen=True, slots=True)
class Selection:
    """The analysis corpus, plus everything discarded to reach it."""

    replicates: list[Replicate]
    excluded: list[Excluded]
    cohort: PromptTriple
    expected_turns: int
    balanced: bool = False

    @property
    def cells(self) -> list[tuple[str, str]]:
        return sorted({(r.topic, r.pair_id) for r in self.replicates})

    def replicates_by_cell(self) -> dict[tuple[str, str], list[Replicate]]:
        out: dict[tuple[str, str], list[Replicate]] = defaultdict(list)
        for rep in self.replicates:
            out[(rep.topic, rep.pair_id)].append(rep)
        return dict(out)


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _count_judgements(run_dir: Path) -> int:
    judgements = run_dir / "judgements"
    if not judgements.is_dir():
        return 0
    return len(list(judgements.glob("turn_*.json")))


def load_runs(
    experiments_dir: Path,
) -> tuple[list[Run], list[Excluded]]:
    """Parse every run directory; drop the ones that are structurally unusable.

    This pass is about completeness only — prompt cohort and pairing come
    later, once we know what the dominant cohort even is.
    """
    runs: list[Run] = []
    excluded: list[Excluded] = []

    if not experiments_dir.is_dir():
        return runs, excluded

    for run_dir in sorted(p for p in experiments_dir.iterdir() if p.is_dir()):
        experiment_id = run_dir.name
        manifest = _read_json(run_dir / "manifest.json")
        if manifest is None:
            excluded.append(
                Excluded(
                    experiment_id, None, None, None,
                    Exclusion.NO_MANIFEST,
                    "manifest.json missing or unreadable",
                )
            )
            continue

        topic = manifest.get("topic")
        pair_id = manifest.get("pair_id")
        condition = manifest.get("condition")
        planned = manifest.get("planned_turns")

        transcript = _read_json(run_dir / "transcript.json")
        if transcript is None:
            excluded.append(
                Excluded(
                    experiment_id, topic, pair_id, condition,
                    Exclusion.NO_TRANSCRIPT,
                    "transcript.json missing — run was interrupted before writing",
                )
            )
            continue

        turn_count = transcript.get("turn_count")
        completed = bool(transcript.get("completed"))
        judgement_count = _count_judgements(run_dir)

        if not completed:
            stopped = transcript.get("stopped_reason") or "unknown reason"
            excluded.append(
                Excluded(
                    experiment_id, topic, pair_id, condition,
                    Exclusion.INCOMPLETE,
                    f"{turn_count}/{planned} turns — {stopped}",
                )
            )
            continue

        if turn_count != planned:
            excluded.append(
                Excluded(
                    experiment_id, topic, pair_id, condition,
                    Exclusion.TURN_COUNT_MISMATCH,
                    f"transcript has {turn_count} turns, manifest planned {planned}",
                )
            )
            continue

        runs.append(
            Run(
                path=run_dir,
                experiment_id=experiment_id,
                topic=topic,
                pair_id=pair_id,
                condition=condition,
                planned_turns=planned,
                turn_count=turn_count,
                completed=completed,
                judgement_count=judgement_count,
                prompts=PromptTriple(
                    behavior=manifest.get("behavior_prompt_sha256"),
                    judge=manifest.get("judge_prompt_sha256"),
                    moderator=manifest.get("moderator_prompt_sha256"),
                ),
                created_at=manifest.get("created_at") or "",
            )
        )

    return runs, excluded


def dominant_cohort(runs: list[Run]) -> PromptTriple:
    """The prompt versions most runs share.

    Behavior and judge prompts are counted over every run; the moderator prompt
    only over treatment runs, since control has none. Picking the mode rather
    than a hardcoded hash means the selection keeps working after the next
    prompt revision — the corpus moves with it instead of silently emptying.
    """
    behavior = Counter(r.prompts.behavior for r in runs)
    judge = Counter(r.prompts.judge for r in runs)
    moderator = Counter(
        r.prompts.moderator for r in runs if r.condition == "treatment"
    )

    def _mode(counter: Counter) -> str | None:
        return counter.most_common(1)[0][0] if counter else None

    return PromptTriple(
        behavior=_mode(behavior),
        judge=_mode(judge),
        moderator=_mode(moderator),
    )


def _in_cohort(run: Run, cohort: PromptTriple) -> bool:
    if run.prompts.behavior != cohort.behavior:
        return False
    if run.prompts.judge != cohort.judge:
        return False
    # Control has no moderator prompt, so there is nothing to match on.
    if run.condition == "treatment" and run.prompts.moderator != cohort.moderator:
        return False
    return True


def _describe_mismatch(run: Run, cohort: PromptTriple) -> str:
    parts = []
    if run.prompts.behavior != cohort.behavior:
        parts.append(f"behavior={_short(run.prompts.behavior)}")
    if run.prompts.judge != cohort.judge:
        parts.append(f"judge={_short(run.prompts.judge)}")
    if run.condition == "treatment" and run.prompts.moderator != cohort.moderator:
        parts.append(f"moderator={_short(run.prompts.moderator)}")
    return "prompt outside cohort: " + ", ".join(parts)


def _short(sha: str | None) -> str:
    return sha[:12] if sha else "none"


def select(
    experiments_dir: Path,
    expected_turns: int = 8,
    cohort: PromptTriple | None = None,
) -> Selection:
    """Build the analysis corpus from the raw experiment directory.

    `expected_turns` is the design's turn count; runs planned at any other
    length were exploratory and are dropped even when internally complete.
    """
    runs, excluded = load_runs(experiments_dir)

    # Runs at a different length were pilots — exclude before finding the
    # cohort, so an old smoke test cannot sway the mode.
    right_length: list[Run] = []
    for run in runs:
        if run.planned_turns != expected_turns:
            excluded.append(
                Excluded(
                    run.experiment_id, run.topic, run.pair_id, run.condition,
                    Exclusion.UNEXPECTED_TURNS,
                    f"planned for {run.planned_turns} turns, analysis expects {expected_turns}",
                )
            )
        else:
            right_length.append(run)

    if cohort is None:
        cohort = dominant_cohort(right_length)

    in_cohort: list[Run] = []
    for run in right_length:
        if _in_cohort(run, cohort):
            in_cohort.append(run)
        else:
            excluded.append(
                Excluded(
                    run.experiment_id, run.topic, run.pair_id, run.condition,
                    Exclusion.PROMPT_MISMATCH,
                    _describe_mismatch(run, cohort),
                )
            )

    # A judged corpus needs one judgement per turn; a run missing some was
    # judged partially, and averaging over what survived would bias the mean.
    judged: list[Run] = []
    for run in in_cohort:
        if run.judgement_count != expected_turns:
            excluded.append(
                Excluded(
                    run.experiment_id, run.topic, run.pair_id, run.condition,
                    Exclusion.MISSING_JUDGEMENTS,
                    f"{run.judgement_count}/{expected_turns} judgement files",
                )
            )
        else:
            judged.append(run)

    replicates, unpaired = _pair_conditions(judged)
    excluded.extend(unpaired)

    return Selection(
        replicates=replicates,
        excluded=excluded,
        cohort=cohort,
        expected_turns=expected_turns,
    )


def _pair_conditions(runs: list[Run]) -> tuple[list[Replicate], list[Excluded]]:
    """Match control to treatment within each cell, chronologically.

    Whatever is left over on either side is dropped: an unmatched run cannot
    enter a within-cell comparison, and keeping it would tilt the condition
    means it does contribute to.
    """
    by_cell: dict[tuple[str, str], dict[str, list[Run]]] = defaultdict(
        lambda: {"control": [], "treatment": []}
    )
    for run in runs:
        if run.condition in ("control", "treatment"):
            by_cell[run.cell][run.condition].append(run)

    replicates: list[Replicate] = []
    unpaired: list[Excluded] = []

    for (topic, pair_id), conditions in sorted(by_cell.items()):
        controls = sorted(conditions["control"], key=lambda r: r.created_at)
        treatments = sorted(conditions["treatment"], key=lambda r: r.created_at)
        matched = min(len(controls), len(treatments))

        for index in range(matched):
            replicates.append(
                Replicate(
                    topic=topic,
                    pair_id=pair_id,
                    index=index + 1,
                    control=controls[index],
                    treatment=treatments[index],
                )
            )

        for leftover in controls[matched:] + treatments[matched:]:
            counterpart = (
                "treatment" if leftover.condition == "control" else "control"
            )
            unpaired.append(
                Excluded(
                    leftover.experiment_id, topic, pair_id, leftover.condition,
                    Exclusion.UNPAIRED_CONDITION,
                    f"no matching {counterpart} replicate in this cell",
                )
            )

    return replicates, unpaired


def balance(selection: Selection) -> Selection:
    """Trim the corpus to an equal design: same cells per topic, same
    replicates per cell.

    Nothing is deleted from disk — the surplus runs move into `excluded` with
    a reason of their own, so the full and balanced analyses can be reported
    side by side. If the conclusion holds under both, the imbalance was not
    driving it.

    Two passes, in order:

    1.  **Cells per topic** — keep the pairs every topic has. Dropping by
        highest pair index keeps the surviving set identical across topics,
        which is what makes between-topic comparison meaningful; the pair
        numbering itself carries no ordering.

    2.  **Replicates per cell** — level every cell to the smallest count,
        keeping the earliest replicates. Chronological order is arbitrary
        here (generation is stochastic), so this is just a stable rule.

    A pass that would empty the corpus is skipped rather than applied: an
    equal design of zero debates answers nothing.
    """
    if not selection.replicates:
        return selection

    dropped: list[Excluded] = []
    kept = list(selection.replicates)

    pairs_by_topic: dict[str, set[str]] = defaultdict(set)
    for rep in kept:
        pairs_by_topic[rep.topic].add(rep.pair_id)

    common_pairs = set.intersection(*pairs_by_topic.values())
    if common_pairs:
        surplus = [r for r in kept if r.pair_id not in common_pairs]
        for rep in surplus:
            present = sorted(t for t, p in pairs_by_topic.items() if rep.pair_id in p)
            dropped.extend(
                _drop_replicate(
                    rep,
                    Exclusion.SURPLUS_CELL,
                    f"{rep.pair_id} present only in {', '.join(present)}",
                )
            )
        kept = [r for r in kept if r.pair_id in common_pairs]

    by_cell: dict[tuple[str, str], list[Replicate]] = defaultdict(list)
    for rep in kept:
        by_cell[(rep.topic, rep.pair_id)].append(rep)

    depth = min(len(reps) for reps in by_cell.values())
    if depth >= 1:
        levelled: list[Replicate] = []
        for cell in sorted(by_cell):
            reps = sorted(by_cell[cell], key=lambda r: r.index)
            levelled.extend(reps[:depth])
            for rep in reps[depth:]:
                dropped.extend(
                    _drop_replicate(
                        rep,
                        Exclusion.SURPLUS_REPLICATE,
                        f"cell has {len(reps)} replicates, design levels to {depth}",
                    )
                )
        kept = levelled

    return Selection(
        replicates=sorted(kept, key=lambda r: (r.topic, r.pair_id, r.index)),
        excluded=selection.excluded + dropped,
        cohort=selection.cohort,
        expected_turns=selection.expected_turns,
        balanced=True,
    )


def _drop_replicate(
    replicate: Replicate, reason: Exclusion, detail: str
) -> list[Excluded]:
    """Both conditions leave together — a replicate is indivisible."""
    return [
        Excluded(
            run.experiment_id, replicate.topic, replicate.pair_id,
            run.condition, reason, detail,
        )
        for run in (replicate.control, replicate.treatment)
    ]
