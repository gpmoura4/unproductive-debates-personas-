"""Build a navigable analysis tree from the selected experiment runs.

Reads only from disk — no API calls, no cost. Writes under analysis/ and never
touches experiments/, which stays append-only.

Run (from the repo root or from debate_simulation/):
    uv run python debate_simulation/scripts/build_analysis.py
    uv run python debate_simulation/scripts/build_analysis.py --balanced
    uv run python debate_simulation/scripts/build_analysis.py --copy --name paper-v1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_SRC = _PROJECT_DIR / "src"

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from analysis.layout import build_tree  # noqa: E402
from analysis.selection import balance, select  # noqa: E402

EXPERIMENTS_DIR = _PROJECT_DIR / "experiments"
ANALYSIS_DIR = _PROJECT_DIR / "analysis"

RULE = "=" * 78


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--turns", type=int, default=8,
        help="turn count the analysis expects (default: 8)",
    )
    parser.add_argument(
        "--balanced", action="store_true",
        help="trim to an equal design before building",
    )
    parser.add_argument(
        "--copy", action="store_true",
        help="copy run directories instead of symlinking them, so the tree "
             "can be zipped and shared off this machine",
    )
    parser.add_argument(
        "--name",
        help="directory name under analysis/runs/ (default: analysis_<stamp>)",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="replace an existing tree of the same name",
    )
    args = parser.parse_args()

    selection = select(EXPERIMENTS_DIR, expected_turns=args.turns)
    if args.balanced:
        selection = balance(selection)

    if not selection.replicates:
        print("Nothing to build: no runs passed selection.")
        print("Check `show_selection.py --excluded` to see why.")
        return 1

    try:
        root = build_tree(
            selection,
            ANALYSIS_DIR,
            run_name=args.name,
            copy=args.copy,
            overwrite=args.overwrite,
        )
    except FileExistsError as e:
        print(f"ERROR: {e}")
        return 1

    by_cell = selection.replicates_by_cell()
    topics = sorted({t for t, _ in by_cell})

    print(RULE)
    print(" ANALYSIS TREE BUILT" + ("  (balanced)" if selection.balanced else ""))
    print(RULE)
    print(f"  path      : {root}")
    print(f"  mode      : {'copies' if args.copy else 'symlinks'}")
    print(f"  topics    : {len(topics)}  ({', '.join(topics)})")
    print(f"  cells     : {len(by_cell)}")
    print(f"  replicates: {len(selection.replicates)}")
    print(f"  debates   : {len(selection.replicates) * 2}")
    print(f"  excluded  : {len(selection.excluded)} runs (see selection.json)")
    print(RULE)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
