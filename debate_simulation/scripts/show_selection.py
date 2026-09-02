"""Show which runs the analysis would use, and why the rest are excluded.

Reads only from disk — no API calls, no cost, nothing written. Run it before
aggregating to check the corpus is what you expect.

Run (from the repo root or from debate_simulation/):
    uv run python debate_simulation/scripts/show_selection.py
    uv run python debate_simulation/scripts/show_selection.py --excluded
    uv run python debate_simulation/scripts/show_selection.py --turns 8
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_SRC = _PROJECT_DIR / "src"

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from analysis.selection import Selection, balance, select  # noqa: E402

EXPERIMENTS_DIR = _PROJECT_DIR / "experiments"

RULE = "=" * 78
THIN = "-" * 78


def _short(sha: str | None) -> str:
    return sha[:12] if sha else "none"


def print_cohort(selection: Selection) -> None:
    print(RULE)
    print(" ANALYSIS COHORT" + ("  (balanced design)" if selection.balanced else ""))
    print(RULE)
    print(f"  behavior prompt  : {_short(selection.cohort.behavior)}")
    print(f"  judge prompt     : {_short(selection.cohort.judge)}")
    print(f"  moderator prompt : {_short(selection.cohort.moderator)}")
    print(f"  turns per debate : {selection.expected_turns}")
    print()


def print_corpus(selection: Selection) -> None:
    by_cell = selection.replicates_by_cell()
    by_topic: dict[str, list] = defaultdict(list)
    for (topic, pair_id), reps in by_cell.items():
        by_topic[topic].append((pair_id, reps))

    print(RULE)
    print(" INCLUDED")
    print(RULE)

    # Compare against the deepest cell anywhere, so a topic that is uniformly
    # thin still stands out against the other topic.
    depth = max((len(reps) for reps in by_cell.values()), default=0)

    for topic in sorted(by_topic):
        pairs = sorted(by_topic[topic])
        n_debates = sum(len(reps) * 2 for _, reps in pairs)
        print(f"\n  {topic}   ({len(pairs)} cells, {n_debates} debates)")
        for pair_id, reps in pairs:
            # Only worth flagging when this cell is thinner than its siblings;
            # a balanced design is uniformly thin on purpose.
            marker = "" if len(reps) == depth else f"   <- {len(reps)} of {depth}"
            print(f"    {pair_id}  x{len(reps)} replicate(s){marker}")
            for rep in reps:
                print(f"      rep-{rep.index}  control   {rep.control.experiment_id}")
                print(f"             treatment {rep.treatment.experiment_id}")

    total_debates = len(selection.replicates) * 2
    print()
    print(THIN)
    print(
        f"  {len(by_cell)} cells   "
        f"{len(selection.replicates)} replicates   "
        f"{total_debates} debates"
    )
    print(THIN)
    print()


def print_excluded(selection: Selection, verbose: bool) -> None:
    if not selection.excluded:
        print("  Nothing excluded.\n")
        return

    by_reason: dict[str, list] = defaultdict(list)
    for item in selection.excluded:
        by_reason[item.reason.value].append(item)

    print(RULE)
    print(f" EXCLUDED  ({len(selection.excluded)} runs)")
    print(RULE)
    for reason in sorted(by_reason):
        items = by_reason[reason]
        print(f"\n  {reason}  ({len(items)})")
        shown = items if verbose else items[:3]
        for item in shown:
            print(f"    {item.experiment_id}")
            print(f"        {item.detail}")
        if not verbose and len(items) > len(shown):
            print(f"    ... and {len(items) - len(shown)} more (--excluded to list)")
    print()


def print_gaps(selection: Selection) -> None:
    """Cells short of the usual two replicates, and topics short of cells."""
    by_cell = selection.replicates_by_cell()
    if not by_cell:
        return

    counts = [len(reps) for reps in by_cell.values()]
    expected = max(counts)
    thin_cells = sorted(
        cell for cell, reps in by_cell.items() if len(reps) < expected
    )

    pairs_per_topic: dict[str, set[str]] = defaultdict(set)
    for topic, pair_id in by_cell:
        pairs_per_topic[topic].add(pair_id)
    all_pairs = set().union(*pairs_per_topic.values())
    missing = {
        topic: sorted(all_pairs - pairs)
        for topic, pairs in pairs_per_topic.items()
        if all_pairs - pairs
    }

    if not thin_cells and not missing:
        return

    print(RULE)
    print(" GAPS")
    print(RULE)
    for topic, pair_id in thin_cells:
        n = len(by_cell[(topic, pair_id)])
        print(f"  {topic} {pair_id}: {n} replicate(s), other cells have {expected}")
    for topic, pairs in sorted(missing.items()):
        for pair_id in pairs:
            print(f"  {topic} {pair_id}: no usable replicate at all")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--turns", type=int, default=8,
        help="turn count the analysis expects (default: 8)",
    )
    parser.add_argument(
        "--excluded", action="store_true",
        help="list every excluded run instead of the first few per reason",
    )
    parser.add_argument(
        "--balanced", action="store_true",
        help="trim to an equal design: same cells per topic, same replicates "
             "per cell (nothing is deleted from disk)",
    )
    args = parser.parse_args()

    selection = select(EXPERIMENTS_DIR, expected_turns=args.turns)
    if args.balanced:
        selection = balance(selection)

    print_cohort(selection)
    print_corpus(selection)
    if not selection.balanced:
        print_gaps(selection)
    print_excluded(selection, verbose=args.excluded)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
