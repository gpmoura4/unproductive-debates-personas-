"""Tests for metric computation.

Builds synthetic runs with known scores under tmp_path, so every expected
value here is arithmetic a reader can check by hand.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis.metrics import (
    activation,
    argument_preservation,
    compute_all,
    judge_consistency,
    load_cells,
    load_debate,
    main_effect,
    per_turn_trajectory,
    score_distribution_by_condition,
)
from analysis.selection import select

from tests.test_selection import make_run


def write_judgements(run_dir: Path, scores: list[list[int]]) -> None:
    """Replace a run's judgements with explicit per-run scores."""
    from statistics import median

    judgements = run_dir / "judgements"
    for path in judgements.glob("*.json"):
        path.unlink()
    for index, runs in enumerate(scores, start=1):
        persona = "persona_1" if index % 2 else "persona_2"
        (judgements / f"turn_{index:03d}_{persona}.json").write_text(
            json.dumps(
                {
                    "turn": index,
                    "persona_id": persona,
                    "summary": {
                        "runs": len(runs),
                        "scores": runs,
                        "median": int(median(runs)),
                        "unanimous": len(set(runs)) == 1,
                    },
                }
            ),
            encoding="utf-8",
        )


def write_transcript_turns(run_dir: Path, turns: list[dict]) -> None:
    """Rewrite a transcript with explicit per-turn moderation flags."""
    transcript = json.loads((run_dir / "transcript.json").read_text())
    transcript["turns"] = turns
    transcript["turn_count"] = len(turns)
    (run_dir / "transcript.json").write_text(
        json.dumps(transcript), encoding="utf-8"
    )


def write_moderation(run_dir: Path, records: list[dict]) -> None:
    """Write moderation records for a treatment run."""
    moderation = run_dir / "moderation"
    moderation.mkdir(exist_ok=True)
    for record in records:
        turn = record["turn"]
        persona = "persona_1" if turn % 2 else "persona_2"
        (moderation / f"turn_{turn:03d}_{persona}.json").write_text(
            json.dumps(record), encoding="utf-8"
        )


def make_scored_cell(
    root: Path,
    *,
    topic: str = "Abortion",
    pair_id: str = "pair-00",
    control_scores: list[int],
    treatment_scores: list[int],
    reformulated: list[bool] | None = None,
) -> None:
    """One replicate with hand-chosen judge scores on both sides."""
    turns = len(control_scores)
    slug = f"{topic[:2].lower()}_{pair_id}"

    control = make_run(
        root, f"{slug}_control", topic=topic, pair_id=pair_id,
        condition="control", planned_turns=turns,
        created_at="2026-09-01T22:00:00-03:00",
    )
    write_judgements(control, [[s, s, s] for s in control_scores])
    write_transcript_turns(
        control,
        [
            {"turn": i, "persona_id": "persona_1" if i % 2 else "persona_2",
             "moderated": False, "was_reformulated": False}
            for i in range(1, turns + 1)
        ],
    )

    treatment = make_run(
        root, f"{slug}_treatment", topic=topic, pair_id=pair_id,
        condition="treatment", planned_turns=turns,
        created_at="2026-09-01T22:30:00-03:00",
    )
    write_judgements(treatment, [[s, s, s] for s in treatment_scores])
    flags = reformulated or [True] * turns
    write_transcript_turns(
        treatment,
        [
            {"turn": i, "persona_id": "persona_1" if i % 2 else "persona_2",
             "moderated": True, "was_reformulated": flags[i - 1]}
            for i in range(1, turns + 1)
        ],
    )
    write_moderation(
        treatment,
        [
            {
                "turn": i,
                "moderation": {
                    "hostility_level": 3,
                    "argument_preserved": "mantida" if flags[i - 1] else "",
                },
                "resolution": {"was_reformulated": flags[i - 1]},
                "consistency_warning": None,
            }
            for i in range(1, turns + 1)
        ],
    )


class TestLoadDebate:
    def test_joins_judgement_and_transcript(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path,
            control_scores=[3, 3, 4, 4, 3, 3, 4, 4],
            treatment_scores=[1, 2, 1, 2, 1, 2, 1, 2],
        )
        selection = select(tmp_path)

        debate = load_debate(selection.replicates[0].control)

        assert len(debate.turns) == 8
        assert debate.turns[0].score == 3
        assert debate.turns[0].moderated is False

    def test_mean_hostility_is_the_average_of_medians(
        self, tmp_path: Path
    ) -> None:
        make_scored_cell(
            tmp_path,
            control_scores=[2, 2, 4, 4, 2, 2, 4, 4],  # mean 3.0
            treatment_scores=[1, 1, 1, 1, 1, 1, 1, 1],
        )
        selection = select(tmp_path)

        debate = load_debate(selection.replicates[0].control)

        assert debate.mean_hostility == 3.0

    def test_treatment_carries_moderator_fields(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path,
            control_scores=[3] * 8,
            treatment_scores=[1] * 8,
        )
        selection = select(tmp_path)

        debate = load_debate(selection.replicates[0].treatment)

        assert debate.turns[0].moderator_score == 3
        assert debate.turns[0].argument_preserved == "mantida"


class TestMainEffect:
    def test_delta_is_treatment_minus_control(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path,
            control_scores=[4] * 8,
            treatment_scores=[1] * 8,
        )

        effect = main_effect(load_cells(select(tmp_path)))

        assert effect["control"]["mean"] == 4.0
        assert effect["treatment"]["mean"] == 1.0
        assert effect["delta"]["mean"] == -3.0

    def test_counts_the_direction_of_each_cell(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path, pair_id="pair-00",
            control_scores=[4] * 8, treatment_scores=[1] * 8,
        )
        make_scored_cell(
            tmp_path, pair_id="pair-01",
            control_scores=[1] * 8, treatment_scores=[3] * 8,
        )

        effect = main_effect(load_cells(select(tmp_path)))

        assert effect["cells_favouring_treatment"] == 1
        assert effect["cells_favouring_control"] == 1

    def test_each_cell_counts_once_regardless_of_turn_count(
        self, tmp_path: Path
    ) -> None:
        """Aggregating over cells, not messages, so a longer debate cannot
        outweigh a shorter one."""
        make_scored_cell(
            tmp_path, pair_id="pair-00",
            control_scores=[4] * 8, treatment_scores=[2] * 8,
        )
        make_scored_cell(
            tmp_path, pair_id="pair-01",
            control_scores=[2] * 8, treatment_scores=[2] * 8,
        )

        effect = main_effect(load_cells(select(tmp_path)))

        assert effect["delta"]["mean"] == -1.0  # (-2 + 0) / 2

    def test_empty_input_reports_nothing(self) -> None:
        effect = main_effect([])

        assert effect["control"]["n"] == 0
        assert effect["delta"]["mean"] is None


class TestPerTurn:
    def test_averages_each_turn_index(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path, pair_id="pair-00",
            control_scores=[1, 2, 3, 4, 1, 2, 3, 4],
            treatment_scores=[0, 0, 0, 0, 0, 0, 0, 0],
        )
        make_scored_cell(
            tmp_path, pair_id="pair-01",
            control_scores=[3, 4, 1, 2, 3, 4, 1, 2],
            treatment_scores=[0, 0, 0, 0, 0, 0, 0, 0],
        )

        trajectory = per_turn_trajectory(load_cells(select(tmp_path)))

        assert trajectory["control"][1]["mean"] == 2.0  # (1 + 3) / 2
        assert trajectory["control"][2]["mean"] == 3.0  # (2 + 4) / 2


class TestActivation:
    def test_counts_moderated_and_reformulated(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path,
            control_scores=[3] * 8,
            treatment_scores=[1] * 8,
            reformulated=[True, True, False, True, False, True, True, True],
        )

        result = activation(load_cells(select(tmp_path)))

        assert result["treatment_turns"] == 8
        assert result["moderated"] == 8
        assert result["reformulated"] == 6
        assert result["reformulated_rate"] == 0.75

    def test_control_turns_are_not_counted(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path, control_scores=[3] * 8, treatment_scores=[1] * 8
        )

        result = activation(load_cells(select(tmp_path)))

        assert result["treatment_turns"] == 8  # not 16

    def test_off_threshold_decisions_are_classified(
        self, tmp_path: Path
    ) -> None:
        make_scored_cell(
            tmp_path, control_scores=[3] * 8, treatment_scores=[1] * 8
        )
        treatment = tmp_path / "ab_pair-00_treatment"
        write_moderation(
            treatment,
            [
                {
                    "turn": 1,
                    "moderation": {"hostility_level": 1, "argument_preserved": "x"},
                    "resolution": {"was_reformulated": True},
                    "consistency_warning": "Intervened at hostility_level 1, below the threshold of 2.",
                },
                {
                    "turn": 2,
                    "moderation": {"hostility_level": 3, "argument_preserved": "x"},
                    "resolution": {"was_reformulated": True},
                    "consistency_warning": "Did not intervene at hostility_level 3, at or above the threshold of 2.",
                },
            ],
        )

        result = activation(load_cells(select(tmp_path)))

        assert result["off_threshold_decisions"] == 2
        breakdown = result["off_threshold_breakdown"]
        assert breakdown["intervened_below_threshold"] == 1
        assert breakdown["declined_at_or_above_threshold"] == 1


class TestJudgeConsistency:
    def test_unanimity_is_counted_over_all_conditions(
        self, tmp_path: Path
    ) -> None:
        make_scored_cell(
            tmp_path, control_scores=[3] * 8, treatment_scores=[1] * 8
        )

        result = judge_consistency(load_cells(select(tmp_path)))

        assert result["messages_scored"] == 16
        assert result["unanimous"] == 16
        assert result["unanimous_rate"] == 1.0

    def test_disagreement_shows_up_in_the_range(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path, control_scores=[3] * 8, treatment_scores=[1] * 8
        )
        control = tmp_path / "ab_pair-00_control"
        write_judgements(control, [[1, 3, 3]] + [[2, 2, 2]] * 7)

        result = judge_consistency(load_cells(select(tmp_path)))

        assert result["range_distribution"]["2"] == 1
        assert result["unanimous"] == 15


class TestScoreDistribution:
    def test_separates_the_conditions(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path,
            control_scores=[4] * 8,
            treatment_scores=[1] * 8,
        )

        distribution = score_distribution_by_condition(load_cells(select(tmp_path)))

        assert distribution["control"]["4"] == 8
        assert distribution["control"]["1"] == 0
        assert distribution["treatment"]["1"] == 8


class TestArgumentPreservation:
    def test_counts_only_reformulated_turns(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path,
            control_scores=[3] * 8,
            treatment_scores=[1] * 8,
            reformulated=[True, True, False, False, True, True, True, True],
        )

        result = argument_preservation(load_cells(select(tmp_path)))

        assert result["reformulations"] == 6
        assert result["preservation_declared"] == 6

    def test_is_flagged_as_self_reported(self, tmp_path: Path) -> None:
        """The rate must never be read as verified preservation."""
        make_scored_cell(
            tmp_path, control_scores=[3] * 8, treatment_scores=[1] * 8
        )

        result = argument_preservation(load_cells(select(tmp_path)))

        assert result["self_reported"] is True


class TestComputeAll:
    def test_produces_every_section(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path, pair_id="pair-00",
            control_scores=[3] * 8, treatment_scores=[1] * 8,
        )
        make_scored_cell(
            tmp_path, topic="Drug Legalization", pair_id="pair-00",
            control_scores=[4] * 8, treatment_scores=[2] * 8,
        )

        metrics = compute_all(select(tmp_path))

        for key in (
            "corpus", "main_effect", "main_effect_by_topic", "per_turn",
            "activation", "judge_consistency", "score_distribution",
            "argument_preservation", "per_cell",
        ):
            assert key in metrics
        assert metrics["corpus"]["debates"] == 4
        assert len(metrics["per_cell"]) == 2

    def test_is_json_serialisable(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path, control_scores=[3] * 8, treatment_scores=[1] * 8
        )

        metrics = compute_all(select(tmp_path))

        json.dumps(metrics)  # must not raise
