"""Tests for the analysis directory tree.

Everything builds fake runs under tmp_path — no test reads or writes the real
experiments/ or analysis/ trees.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis.layout import build_tree, default_run_name, slugify
from analysis.selection import balance, select

from tests.test_selection import make_replicated_cell, make_run


@pytest.fixture
def corpus(tmp_path: Path) -> tuple[Path, Path]:
    """Two topics, two pairs each, two replicates per cell."""
    experiments = tmp_path / "experiments"
    experiments.mkdir()
    for pair in ("pair-00", "pair-01"):
        make_replicated_cell(experiments, "Abortion", pair, 2)
        make_replicated_cell(experiments, "Drug Legalization", pair, 2)
    return experiments, tmp_path / "analysis"


class TestSlugify:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("Abortion", "abortion"),
            ("Drug Legalization", "drug-legalization"),
            ("Gun Ownership", "gun-ownership"),
            ("  Spaced  Out  ", "spaced-out"),
            ("Punctuation!?", "punctuation"),
        ],
    )
    def test_makes_filesystem_safe_names(self, raw: str, expected: str) -> None:
        assert slugify(raw) == expected

    def test_falls_back_when_nothing_survives(self) -> None:
        assert slugify("!!!") == "untitled"


class TestBuildTree:
    def test_lays_out_topic_pair_replicate_condition(
        self, corpus: tuple[Path, Path]
    ) -> None:
        experiments, analysis = corpus

        root = build_tree(select(experiments), analysis, run_name="run")

        leaf = root / "by_topic" / "abortion" / "pair-00" / "rep-1" / "control"
        assert leaf.is_dir()
        assert (leaf / "transcript.json").is_file()

    def test_both_conditions_are_present(self, corpus: tuple[Path, Path]) -> None:
        experiments, analysis = corpus

        root = build_tree(select(experiments), analysis, run_name="run")

        rep = root / "by_topic" / "drug-legalization" / "pair-01" / "rep-2"
        assert (rep / "control").is_dir()
        assert (rep / "treatment").is_dir()

    def test_symlinks_by_default(self, corpus: tuple[Path, Path]) -> None:
        experiments, analysis = corpus

        root = build_tree(select(experiments), analysis, run_name="run")

        leaf = root / "by_topic" / "abortion" / "pair-00" / "rep-1" / "control"
        assert leaf.is_symlink()

    def test_symlinks_are_relative(self, corpus: tuple[Path, Path]) -> None:
        """Absolute links would break as soon as the project moves."""
        experiments, analysis = corpus

        root = build_tree(select(experiments), analysis, run_name="run")

        leaf = root / "by_topic" / "abortion" / "pair-00" / "rep-1" / "control"
        assert not Path(leaf.readlink()).is_absolute()

    def test_copy_mode_makes_real_directories(
        self, corpus: tuple[Path, Path]
    ) -> None:
        experiments, analysis = corpus

        root = build_tree(select(experiments), analysis, run_name="run", copy=True)

        leaf = root / "by_topic" / "abortion" / "pair-00" / "rep-1" / "control"
        assert leaf.is_dir()
        assert not leaf.is_symlink()
        assert (leaf / "transcript.json").is_file()

    def test_copies_survive_the_source_disappearing(
        self, corpus: tuple[Path, Path]
    ) -> None:
        """The property that makes copy mode worth having."""
        import shutil

        experiments, analysis = corpus
        root = build_tree(select(experiments), analysis, run_name="run", copy=True)
        shutil.rmtree(experiments)

        leaf = root / "by_topic" / "abortion" / "pair-00" / "rep-1" / "control"
        assert (leaf / "transcript.json").is_file()

    def test_writes_a_selection_record(self, corpus: tuple[Path, Path]) -> None:
        experiments, analysis = corpus

        root = build_tree(select(experiments), analysis, run_name="run")

        document = json.loads((root / "selection.json").read_text())
        assert document["totals"]["cells"] == 4
        assert document["totals"]["replicates"] == 8
        assert document["totals"]["debates"] == 16
        assert document["balanced"] is False

    def test_record_names_both_runs_of_each_replicate(
        self, corpus: tuple[Path, Path]
    ) -> None:
        experiments, analysis = corpus

        root = build_tree(select(experiments), analysis, run_name="run")

        document = json.loads((root / "selection.json").read_text())
        entry = document["included"][0]
        assert entry["control"].endswith("_control")
        assert entry["treatment"].endswith("_treatment")
        assert (root / entry["path"]).is_dir()

    def test_record_carries_the_exclusions(self, tmp_path: Path) -> None:
        experiments = tmp_path / "experiments"
        experiments.mkdir()
        make_replicated_cell(experiments, "Abortion", "pair-00", 1)
        make_run(experiments, "cut_treatment", condition="treatment",
                 pair_id="pair-09", turn_count=5, completed=False)

        root = build_tree(select(experiments), tmp_path / "analysis", run_name="run")

        document = json.loads((root / "selection.json").read_text())
        reasons = {e["reason"] for e in document["excluded"]}
        assert "incomplete" in reasons

    def test_balanced_flag_is_recorded(self, tmp_path: Path) -> None:
        experiments = tmp_path / "experiments"
        experiments.mkdir()
        make_replicated_cell(experiments, "Abortion", "pair-00", 2)
        make_replicated_cell(experiments, "Drug Legalization", "pair-00", 1)

        root = build_tree(
            balance(select(experiments)), tmp_path / "analysis", run_name="run"
        )

        document = json.loads((root / "selection.json").read_text())
        assert document["balanced"] is True
        assert document["totals"]["replicates"] == 2

    def test_refuses_to_replace_an_existing_tree(
        self, corpus: tuple[Path, Path]
    ) -> None:
        experiments, analysis = corpus
        selection = select(experiments)
        build_tree(selection, analysis, run_name="run")

        with pytest.raises(FileExistsError):
            build_tree(selection, analysis, run_name="run")

    def test_overwrite_replaces_it(self, corpus: tuple[Path, Path]) -> None:
        experiments, analysis = corpus
        selection = select(experiments)
        root = build_tree(selection, analysis, run_name="run")
        (root / "stale.txt").write_text("left over", encoding="utf-8")

        build_tree(selection, analysis, run_name="run", overwrite=True)

        assert not (root / "stale.txt").exists()
        assert (root / "selection.json").is_file()

    def test_never_writes_into_experiments(
        self, corpus: tuple[Path, Path]
    ) -> None:
        experiments, analysis = corpus
        before = sorted(p.name for p in experiments.iterdir())

        build_tree(select(experiments), analysis, run_name="run")

        assert sorted(p.name for p in experiments.iterdir()) == before

    def test_two_analyses_coexist(self, corpus: tuple[Path, Path]) -> None:
        experiments, analysis = corpus
        selection = select(experiments)

        full = build_tree(selection, analysis, run_name="full")
        trimmed = build_tree(balance(selection), analysis, run_name="trimmed")

        assert full.is_dir()
        assert trimmed.is_dir()
        assert full != trimmed


class TestDefaultRunName:
    def test_is_timestamped(self) -> None:
        from datetime import datetime

        name = default_run_name(datetime(2026, 9, 2, 14, 30, 5))

        assert name == "analysis_20260902-143005"
