"""Tests for the worked-example slide sequence.

Rendering is exercised end to end (matplotlib writes real PNGs under tmp_path)
but assertions are about selection and structure, not pixels.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis.metrics import load_cells
from analysis.selection import select
from analysis.showcase import build_showcase, pick_example

from tests.test_metrics import make_scored_cell


class TestPickExample:
    def test_prefers_the_steepest_escalation(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path, pair_id="pair-00",
            control_scores=[1, 2, 2, 3, 3, 4, 4, 4],  # escalates +3
            treatment_scores=[1] * 8,
        )
        make_scored_cell(
            tmp_path, pair_id="pair-01",
            control_scores=[3, 3, 3, 3, 3, 3, 3, 3],  # flat
            treatment_scores=[1] * 8,
        )

        ranked = pick_example(load_cells(select(tmp_path)))

        assert ranked[0].cell.pair_id == "pair-00"
        assert ranked[0].escalation == 3

    def test_breaks_ties_by_closeness_to_the_mean_delta(
        self, tmp_path: Path
    ) -> None:
        """An example should be representative, not the most extreme case."""
        make_scored_cell(
            tmp_path, pair_id="pair-00",
            control_scores=[1, 2, 2, 3, 3, 4, 4, 4],
            treatment_scores=[0] * 8,  # delta -2.875, extreme
        )
        make_scored_cell(
            tmp_path, pair_id="pair-01",
            control_scores=[1, 2, 2, 3, 3, 4, 4, 4],
            treatment_scores=[2] * 8,  # delta -0.875, nearer the mean
        )
        make_scored_cell(
            tmp_path, pair_id="pair-02",
            control_scores=[1, 2, 2, 3, 3, 4, 4, 4],
            treatment_scores=[2] * 8,
        )

        ranked = pick_example(load_cells(select(tmp_path)))

        assert ranked[0].cell.pair_id in {"pair-01", "pair-02"}

    def test_topic_filter_overrides_the_ranking(self, tmp_path: Path) -> None:
        make_scored_cell(
            tmp_path, topic="Abortion", pair_id="pair-00",
            control_scores=[1, 2, 2, 3, 3, 4, 4, 4],
            treatment_scores=[1] * 8,
        )
        make_scored_cell(
            tmp_path, topic="Drug Legalization", pair_id="pair-00",
            control_scores=[3] * 8,
            treatment_scores=[1] * 8,
        )

        ranked = pick_example(
            load_cells(select(tmp_path)), topic="Drug Legalization"
        )

        assert len(ranked) == 1
        assert ranked[0].cell.topic == "Drug Legalization"

    def test_pair_filter_narrows_to_one_cell(self, tmp_path: Path) -> None:
        for pair in ("pair-00", "pair-01"):
            make_scored_cell(
                tmp_path, pair_id=pair,
                control_scores=[3] * 8, treatment_scores=[1] * 8,
            )

        ranked = pick_example(load_cells(select(tmp_path)), pair_id="pair-01")

        assert len(ranked) == 1
        assert ranked[0].cell.pair_id == "pair-01"

    def test_empty_input_ranks_nothing(self) -> None:
        assert pick_example([]) == []


class TestBuildShowcase:
    @pytest.fixture
    def corpus(self, tmp_path: Path) -> Path:
        experiments = tmp_path / "experiments"
        experiments.mkdir()
        make_scored_cell(
            experiments, topic="Drug Legalization", pair_id="pair-00",
            control_scores=[1, 2, 2, 3, 3, 4, 4, 4],
            treatment_scores=[1, 1, 2, 1, 2, 2, 3, 3],
        )
        return experiments

    def test_writes_a_numbered_page_sequence(
        self, corpus: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "examples"

        result = build_showcase(select(corpus), out)

        pages = sorted(p.name for p in out.glob("*.png"))
        assert pages[0].startswith("p01_capa")
        assert pages[-1].endswith("comparacao.png")
        assert len(result["pages"]) == len(pages)

    def test_pages_are_written_in_order(self, corpus: Path, tmp_path: Path) -> None:
        out = tmp_path / "examples"

        result = build_showcase(select(corpus), out)

        numbers = [int(p.name[1:3]) for p in result["pages"]]
        assert numbers == sorted(numbers)
        assert numbers == list(range(1, len(numbers) + 1))

    def test_turns_per_page_controls_the_page_count(
        self, corpus: Path, tmp_path: Path
    ) -> None:
        few = build_showcase(select(corpus), tmp_path / "a", turns_per_page=2)
        many = build_showcase(select(corpus), tmp_path / "b", turns_per_page=4)

        assert len(few["pages"]) > len(many["pages"])

    def test_writes_the_markdown_companion(
        self, corpus: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "examples"

        build_showcase(select(corpus), out)

        markdown = (out / "exemplo.md").read_text(encoding="utf-8")
        assert "Controle — sem moderação" in markdown
        assert "Tratamento — com moderação D5" in markdown

    def test_markdown_escapes_pipes_in_message_text(
        self, tmp_path: Path
    ) -> None:
        """A pipe in a debater's message would break the Markdown table."""
        experiments = tmp_path / "experiments"
        experiments.mkdir()
        make_scored_cell(
            experiments, control_scores=[3] * 8, treatment_scores=[1] * 8,
        )
        control = experiments / "ab_pair-00_control"
        transcript = json.loads((control / "transcript.json").read_text())
        transcript["turns"][0]["published_text"] = "a | b | c"
        (control / "transcript.json").write_text(json.dumps(transcript))

        out = tmp_path / "examples"
        build_showcase(select(experiments), out)

        markdown = (out / "exemplo.md").read_text(encoding="utf-8")
        assert "a \\| b \\| c" in markdown

    def test_reports_the_chosen_cell(self, corpus: Path, tmp_path: Path) -> None:
        result = build_showcase(select(corpus), tmp_path / "examples")

        assert result["example"].cell.pair_id == "pair-00"
        assert result["example"].escalation == 3

    def test_unmatched_filter_produces_nothing(
        self, corpus: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "examples"

        result = build_showcase(select(corpus), out, topic="Gun Ownership")

        assert result["pages"] == []
        assert result["example"] is None

    def test_empty_selection_produces_nothing(self, tmp_path: Path) -> None:
        experiments = tmp_path / "experiments"
        experiments.mkdir()

        result = build_showcase(select(experiments), tmp_path / "examples")

        assert result["pages"] == []
