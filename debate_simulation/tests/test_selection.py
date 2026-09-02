"""Tests for analysis run selection.

Everything builds fake run directories under tmp_path — no test reads the real
experiments/ tree, so the corpus on disk can change without breaking these.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis.selection import (
    Exclusion,
    PromptTriple,
    balance,
    dominant_cohort,
    load_runs,
    select,
)

BEHAVIOR = "b" * 64
JUDGE = "j" * 64
MODERATOR = "m" * 64


def make_run(
    root: Path,
    experiment_id: str,
    *,
    topic: str = "Abortion",
    pair_id: str = "pair-00",
    condition: str = "control",
    planned_turns: int = 8,
    turn_count: int | None = None,
    completed: bool = True,
    judgements: int | None = None,
    behavior: str | None = BEHAVIOR,
    judge: str | None = JUDGE,
    moderator: str | None = None,
    created_at: str = "2026-09-01T22:00:00-03:00",
    write_transcript: bool = True,
    write_manifest: bool = True,
    stopped_reason: str | None = None,
) -> Path:
    """Build one run directory complete enough for selection to parse."""
    run_dir = root / experiment_id
    run_dir.mkdir(parents=True)

    if turn_count is None:
        turn_count = planned_turns
    if judgements is None:
        judgements = turn_count
    if moderator is None and condition == "treatment":
        moderator = MODERATOR

    if write_manifest:
        (run_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "experiment_id": experiment_id,
                    "created_at": created_at,
                    "condition": condition,
                    "topic": topic,
                    "pair_id": pair_id,
                    "planned_turns": planned_turns,
                    "behavior_prompt_sha256": behavior,
                    "judge_prompt_sha256": judge,
                    "moderator_prompt_sha256": moderator,
                }
            ),
            encoding="utf-8",
        )

    if write_transcript:
        (run_dir / "transcript.json").write_text(
            json.dumps(
                {
                    "experiment_id": experiment_id,
                    "turn_count": turn_count,
                    "completed": completed,
                    "stopped_reason": stopped_reason,
                    "turns": [],
                }
            ),
            encoding="utf-8",
        )

    if judgements:
        judge_dir = run_dir / "judgements"
        judge_dir.mkdir()
        for turn in range(1, judgements + 1):
            persona = "persona_1" if turn % 2 else "persona_2"
            (judge_dir / f"turn_{turn:03d}_{persona}.json").write_text(
                json.dumps({"turn": turn}), encoding="utf-8"
            )

    return run_dir


def make_cell(root: Path, prefix: str, **kwargs) -> None:
    """A matched control+treatment pair for one cell."""
    make_run(root, f"{prefix}_control", condition="control", **kwargs)
    make_run(root, f"{prefix}_treatment", condition="treatment", **kwargs)


class TestLoadRuns:
    def test_reads_a_complete_run(self, tmp_path: Path) -> None:
        make_run(tmp_path, "20260901-220209_abortion_pair-00_control")

        runs, excluded = load_runs(tmp_path)

        assert len(runs) == 1
        assert not excluded
        assert runs[0].topic == "Abortion"
        assert runs[0].cell == ("Abortion", "pair-00")

    def test_missing_manifest_is_excluded(self, tmp_path: Path) -> None:
        make_run(tmp_path, "run_a", write_manifest=False)

        runs, excluded = load_runs(tmp_path)

        assert not runs
        assert excluded[0].reason is Exclusion.NO_MANIFEST

    def test_missing_transcript_is_excluded(self, tmp_path: Path) -> None:
        make_run(tmp_path, "run_a", write_transcript=False)

        runs, excluded = load_runs(tmp_path)

        assert not runs
        assert excluded[0].reason is Exclusion.NO_TRANSCRIPT

    def test_interrupted_run_keeps_its_stop_reason(self, tmp_path: Path) -> None:
        make_run(
            tmp_path, "run_a",
            turn_count=5, completed=False,
            stopped_reason="APITimeoutError: Request timed out.",
        )

        runs, excluded = load_runs(tmp_path)

        assert not runs
        assert excluded[0].reason is Exclusion.INCOMPLETE
        assert "5/8 turns" in excluded[0].detail
        assert "APITimeoutError" in excluded[0].detail

    def test_turn_count_disagreeing_with_manifest_is_excluded(
        self, tmp_path: Path
    ) -> None:
        # completed=True but short: the transcript contradicts its own manifest.
        make_run(tmp_path, "run_a", planned_turns=8, turn_count=6, judgements=6)

        runs, excluded = load_runs(tmp_path)

        assert not runs
        assert excluded[0].reason is Exclusion.TURN_COUNT_MISMATCH


class TestDominantCohort:
    def test_picks_the_majority_prompt_versions(self, tmp_path: Path) -> None:
        for i in range(3):
            make_run(tmp_path, f"new_{i}", condition="treatment")
        make_run(
            tmp_path, "old_0", condition="treatment",
            behavior="x" * 64, judge="y" * 64, moderator="z" * 64,
        )

        runs, _ = load_runs(tmp_path)
        cohort = dominant_cohort(runs)

        assert cohort == PromptTriple(BEHAVIOR, JUDGE, MODERATOR)

    def test_control_runs_do_not_vote_on_the_moderator_prompt(
        self, tmp_path: Path
    ) -> None:
        # Controls carry moderator=None; if they counted, None would win.
        for i in range(5):
            make_run(tmp_path, f"control_{i}", condition="control")
        make_run(tmp_path, "treatment_0", condition="treatment")

        runs, _ = load_runs(tmp_path)

        assert dominant_cohort(runs).moderator == MODERATOR


class TestSelect:
    def test_pairs_control_with_treatment(self, tmp_path: Path) -> None:
        make_cell(tmp_path, "20260901-220209_abortion_pair-00")

        selection = select(tmp_path)

        assert len(selection.replicates) == 1
        rep = selection.replicates[0]
        assert rep.index == 1
        assert rep.control.condition == "control"
        assert rep.treatment.condition == "treatment"

    def test_two_replicates_are_matched_chronologically(
        self, tmp_path: Path
    ) -> None:
        make_run(
            tmp_path, "a_control", condition="control",
            created_at="2026-09-01T22:02:09-03:00",
        )
        make_run(
            tmp_path, "b_control", condition="control",
            created_at="2026-09-01T22:03:17-03:00",
        )
        make_run(
            tmp_path, "a_treatment", condition="treatment",
            created_at="2026-09-01T22:28:49-03:00",
        )
        make_run(
            tmp_path, "b_treatment", condition="treatment",
            created_at="2026-09-01T22:29:28-03:00",
        )

        selection = select(tmp_path)

        assert len(selection.replicates) == 2
        first, second = selection.replicates
        assert first.control.experiment_id == "a_control"
        assert first.treatment.experiment_id == "a_treatment"
        assert second.control.experiment_id == "b_control"
        assert second.treatment.experiment_id == "b_treatment"

    def test_orphaned_control_is_dropped_with_its_treatment(
        self, tmp_path: Path
    ) -> None:
        """The pair-04 case: treatment times out, so its control goes too."""
        make_run(tmp_path, "ok_control", condition="control",
                 created_at="2026-09-02T08:04:29-03:00")
        make_run(tmp_path, "ok_treatment", condition="treatment",
                 created_at="2026-09-02T08:26:49-03:00")
        make_run(tmp_path, "orphan_control", condition="control",
                 created_at="2026-09-02T08:10:03-03:00")
        make_run(tmp_path, "cut_treatment", condition="treatment",
                 turn_count=5, completed=False,
                 created_at="2026-09-02T08:39:01-03:00")

        selection = select(tmp_path)

        assert len(selection.replicates) == 1
        reasons = {e.experiment_id: e.reason for e in selection.excluded}
        assert reasons["cut_treatment"] is Exclusion.INCOMPLETE
        assert reasons["orphan_control"] is Exclusion.UNPAIRED_CONDITION

    def test_runs_at_other_lengths_are_excluded(self, tmp_path: Path) -> None:
        make_cell(tmp_path, "smoke", planned_turns=1)
        make_cell(tmp_path, "pilot", planned_turns=10)
        make_cell(tmp_path, "real", planned_turns=8)

        selection = select(tmp_path, expected_turns=8)

        assert len(selection.replicates) == 1
        assert selection.replicates[0].control.experiment_id == "real_control"
        wrong_length = [
            e for e in selection.excluded
            if e.reason is Exclusion.UNEXPECTED_TURNS
        ]
        assert len(wrong_length) == 4

    def test_short_pilots_do_not_sway_the_cohort(self, tmp_path: Path) -> None:
        """Length is filtered first, so old prompts cannot win the vote."""
        for i in range(4):
            make_cell(
                tmp_path, f"pilot_{i}", planned_turns=3,
                behavior="x" * 64, judge="y" * 64, moderator="z" * 64,
            )
        make_cell(tmp_path, "real")

        selection = select(tmp_path, expected_turns=8)

        assert selection.cohort == PromptTriple(BEHAVIOR, JUDGE, MODERATOR)
        assert len(selection.replicates) == 1

    def test_older_prompt_version_is_excluded(self, tmp_path: Path) -> None:
        make_cell(tmp_path, "new_a")
        make_cell(tmp_path, "new_b", pair_id="pair-01")
        make_cell(tmp_path, "old", pair_id="pair-02", behavior="x" * 64)

        selection = select(tmp_path)

        assert len(selection.replicates) == 2
        mismatched = [
            e for e in selection.excluded
            if e.reason is Exclusion.PROMPT_MISMATCH
        ]
        assert len(mismatched) == 2
        assert "behavior=" in mismatched[0].detail

    def test_partially_judged_run_is_excluded(self, tmp_path: Path) -> None:
        make_run(tmp_path, "half_control", condition="control", judgements=2)
        make_run(tmp_path, "half_treatment", condition="treatment")

        selection = select(tmp_path)

        assert not selection.replicates
        reasons = {e.experiment_id: e.reason for e in selection.excluded}
        assert reasons["half_control"] is Exclusion.MISSING_JUDGEMENTS
        assert reasons["half_treatment"] is Exclusion.UNPAIRED_CONDITION

    def test_explicit_cohort_overrides_the_majority(self, tmp_path: Path) -> None:
        make_cell(tmp_path, "majority")
        make_cell(
            tmp_path, "wanted", pair_id="pair-01",
            behavior="x" * 64, judge="y" * 64, moderator="z" * 64,
        )

        selection = select(
            tmp_path,
            cohort=PromptTriple("x" * 64, "y" * 64, "z" * 64),
        )

        assert len(selection.replicates) == 1
        assert selection.replicates[0].pair_id == "pair-01"

    def test_cells_span_topics(self, tmp_path: Path) -> None:
        make_cell(tmp_path, "ab", topic="Abortion", pair_id="pair-00")
        make_cell(tmp_path, "dl", topic="Drug Legalization", pair_id="pair-00")

        selection = select(tmp_path)

        assert selection.cells == [
            ("Abortion", "pair-00"),
            ("Drug Legalization", "pair-00"),
        ]

    def test_empty_directory_selects_nothing(self, tmp_path: Path) -> None:
        selection = select(tmp_path)

        assert not selection.replicates
        assert not selection.excluded

    def test_missing_directory_selects_nothing(self, tmp_path: Path) -> None:
        selection = select(tmp_path / "does_not_exist")

        assert not selection.replicates


def make_replicated_cell(
    root: Path, topic: str, pair_id: str, count: int
) -> None:
    """`count` matched replicates of one cell, in chronological order."""
    slug = f"{topic[:2].lower()}_{pair_id}"
    for i in range(count):
        stamp = f"2026-09-0{i + 1}T22:00:00-03:00"
        for condition in ("control", "treatment"):
            make_run(
                root, f"{slug}_rep{i}_{condition}",
                topic=topic, pair_id=pair_id, condition=condition,
                created_at=stamp,
            )


class TestBalance:
    def test_levels_replicates_to_the_thinnest_cell(self, tmp_path: Path) -> None:
        make_replicated_cell(tmp_path, "Abortion", "pair-00", 2)
        make_replicated_cell(tmp_path, "Drug Legalization", "pair-00", 1)

        balanced = balance(select(tmp_path))

        counts = {c: len(r) for c, r in balanced.replicates_by_cell().items()}
        assert set(counts.values()) == {1}
        assert balanced.balanced is True

    def test_drops_cells_a_topic_does_not_share(self, tmp_path: Path) -> None:
        """The pair-05 case: Abortion has it, Drug Legalization does not."""
        for pair in ("pair-00", "pair-01"):
            make_replicated_cell(tmp_path, "Abortion", pair, 1)
            make_replicated_cell(tmp_path, "Drug Legalization", pair, 1)
        make_replicated_cell(tmp_path, "Abortion", "pair-05", 1)

        balanced = balance(select(tmp_path))

        assert {p for _, p in balanced.cells} == {"pair-00", "pair-01"}
        surplus = [
            e for e in balanced.excluded
            if e.reason is Exclusion.SURPLUS_CELL
        ]
        assert len(surplus) == 2  # both conditions of the dropped replicate
        assert all(e.pair_id == "pair-05" for e in surplus)

    def test_keeps_the_earliest_replicates(self, tmp_path: Path) -> None:
        make_replicated_cell(tmp_path, "Abortion", "pair-00", 3)
        make_replicated_cell(tmp_path, "Drug Legalization", "pair-00", 1)

        balanced = balance(select(tmp_path))

        kept = [r for r in balanced.replicates if r.topic == "Abortion"]
        assert len(kept) == 1
        assert kept[0].index == 1

    def test_a_replicate_leaves_with_both_conditions(self, tmp_path: Path) -> None:
        make_replicated_cell(tmp_path, "Abortion", "pair-00", 2)
        make_replicated_cell(tmp_path, "Drug Legalization", "pair-00", 1)

        balanced = balance(select(tmp_path))

        surplus = [
            e for e in balanced.excluded
            if e.reason is Exclusion.SURPLUS_REPLICATE
        ]
        assert {e.condition for e in surplus} == {"control", "treatment"}

    def test_already_equal_design_is_untouched(self, tmp_path: Path) -> None:
        for pair in ("pair-00", "pair-01"):
            make_replicated_cell(tmp_path, "Abortion", pair, 2)
            make_replicated_cell(tmp_path, "Drug Legalization", pair, 2)

        selection = select(tmp_path)
        balanced = balance(selection)

        assert len(balanced.replicates) == len(selection.replicates)
        assert len(balanced.excluded) == len(selection.excluded)

    def test_single_topic_keeps_every_cell(self, tmp_path: Path) -> None:
        # With one topic the intersection is that topic's own pairs, so the
        # cell pass must not drop anything.
        for pair in ("pair-00", "pair-01", "pair-02"):
            make_replicated_cell(tmp_path, "Abortion", pair, 1)

        balanced = balance(select(tmp_path))

        assert len(balanced.cells) == 3

    def test_disjoint_topics_are_left_alone(self, tmp_path: Path) -> None:
        """No shared pair at all: balancing would empty the corpus."""
        make_replicated_cell(tmp_path, "Abortion", "pair-00", 1)
        make_replicated_cell(tmp_path, "Drug Legalization", "pair-01", 1)

        balanced = balance(select(tmp_path))

        assert len(balanced.replicates) == 2
        assert not [
            e for e in balanced.excluded
            if e.reason is Exclusion.SURPLUS_CELL
        ]

    def test_empty_selection_is_returned_unchanged(self, tmp_path: Path) -> None:
        selection = select(tmp_path)

        balanced = balance(selection)

        assert not balanced.replicates
        assert balanced.balanced is False

    def test_original_selection_is_not_mutated(self, tmp_path: Path) -> None:
        make_replicated_cell(tmp_path, "Abortion", "pair-00", 2)
        make_replicated_cell(tmp_path, "Drug Legalization", "pair-00", 1)

        selection = select(tmp_path)
        before = len(selection.replicates)
        balance(selection)

        assert len(selection.replicates) == before
        assert selection.balanced is False
