"""Materialise a selected corpus as a navigable directory tree.

`experiments/` is append-only and flat: every run ever executed, named by
timestamp, in one directory. That is the right shape for a log — nothing is
ever rewritten, so it stays trustworthy as evidence — and the wrong shape for
reading. Finding "the treatment side of Abortion pair-03, second replicate"
means scanning sixty directory names for a timestamp.

This module writes the other view: topic, then pair, then replicate, then
condition. It never writes into `experiments/`; each leaf is a symlink back to
the run directory, or a copy when the tree has to leave this machine.

    analysis/runs/<run-name>/
      selection.json              what was included, excluded, and why
      by_topic/
        abortion/
          pair-00/
            rep-1/
              control/     -> experiments/20260901-220209_..._control
              treatment/   -> experiments/20260901-222849_..._treatment
            rep-2/
              ...

Regenerating is cheap and non-destructive: the tree is derived, so it can be
rebuilt whenever the selection criteria change.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from analysis.selection import Replicate, Selection


def slugify(text: str) -> str:
    """Filesystem-safe topic name: "Drug Legalization" -> "drug-legalization"."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug or "untitled"


def default_run_name(now: datetime | None = None) -> str:
    """A dated, sequential name so successive analyses sort chronologically."""
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    return f"analysis_{stamp}"


def _link_or_copy(source: Path, destination: Path, copy: bool) -> None:
    """Point `destination` at `source`, by copy or by relative symlink.

    Symlinks are made relative so the tree survives being moved as a whole
    alongside `experiments/` — an absolute link would break the moment the
    project directory is renamed.
    """
    if copy:
        shutil.copytree(source, destination)
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    relative = os.path.relpath(source.resolve(), destination.parent.resolve())
    destination.symlink_to(relative, target_is_directory=True)


def _replicate_dir(root: Path, replicate: Replicate) -> Path:
    return (
        root
        / "by_topic"
        / slugify(replicate.topic)
        / replicate.pair_id
        / f"rep-{replicate.index}"
    )


def _selection_document(selection: Selection, root: Path) -> dict:
    """The record of what this tree contains and how it was derived.

    Written alongside the tree so the corpus can be audited without rerunning
    the selection — and so a reader can see the exclusions, which are the part
    a directory listing cannot show.
    """
    by_cell = selection.replicates_by_cell()
    return {
        "created_at": datetime.now().astimezone().isoformat(),
        "balanced": selection.balanced,
        "expected_turns": selection.expected_turns,
        "cohort": {
            "behavior_prompt_sha256": selection.cohort.behavior,
            "judge_prompt_sha256": selection.cohort.judge,
            "moderator_prompt_sha256": selection.cohort.moderator,
        },
        "totals": {
            "topics": len({t for t, _ in by_cell}),
            "cells": len(by_cell),
            "replicates": len(selection.replicates),
            "debates": len(selection.replicates) * 2,
            "excluded_runs": len(selection.excluded),
        },
        "included": [
            {
                "topic": rep.topic,
                "pair_id": rep.pair_id,
                "replicate": rep.index,
                "path": str(
                    _replicate_dir(root, rep).relative_to(root)
                ),
                "control": rep.control.experiment_id,
                "treatment": rep.treatment.experiment_id,
            }
            for rep in selection.replicates
        ],
        "excluded": [
            {**asdict(item), "reason": item.reason.value}
            for item in selection.excluded
        ],
    }


def build_tree(
    selection: Selection,
    analysis_dir: Path,
    run_name: str | None = None,
    copy: bool = False,
    overwrite: bool = False,
) -> Path:
    """Write the selected corpus as `analysis/runs/<run_name>/`.

    Returns the created directory. Raises FileExistsError on an existing name
    unless `overwrite` is set — analyses are cheap to regenerate, but silently
    replacing one you meant to keep is not a recoverable mistake.
    """
    run_name = run_name or default_run_name()
    root = analysis_dir / "runs" / run_name

    if root.exists():
        if not overwrite:
            raise FileExistsError(
                f"{root} already exists — pass overwrite=True to replace it"
            )
        shutil.rmtree(root)

    root.mkdir(parents=True)

    for replicate in selection.replicates:
        rep_dir = _replicate_dir(root, replicate)
        rep_dir.mkdir(parents=True, exist_ok=True)
        _link_or_copy(replicate.control.path, rep_dir / "control", copy)
        _link_or_copy(replicate.treatment.path, rep_dir / "treatment", copy)

    document = _selection_document(selection, root)
    (root / "selection.json").write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return root
