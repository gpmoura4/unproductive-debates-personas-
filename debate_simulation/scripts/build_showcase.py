"""Build the slide sequence for one worked example debate.

Reads only from disk — no API calls, no cost. Writes PNG pages plus a Markdown
version under analysis/runs/<run>/examples/.

Run (from the repo root or from debate_simulation/):
    uv run python debate_simulation/scripts/build_showcase.py
    uv run python debate_simulation/scripts/build_showcase.py --list
    uv run python debate_simulation/scripts/build_showcase.py --topic "Abortion" --pair pair-02
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_SRC = _PROJECT_DIR / "src"

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from analysis.metrics import load_cells  # noqa: E402
from analysis.selection import balance, select  # noqa: E402
from analysis.showcase import build_showcase, pick_example  # noqa: E402

EXPERIMENTS_DIR = _PROJECT_DIR / "experiments"
ANALYSIS_DIR = _PROJECT_DIR / "analysis"

RULE = "=" * 78


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", type=int, default=8)
    parser.add_argument(
        "--full", action="store_true",
        help="use the complete corpus instead of the balanced design",
    )
    parser.add_argument("--topic", help="force a topic (e.g. \"Abortion\")")
    parser.add_argument("--pair", help="force a pair (e.g. pair-03)")
    parser.add_argument(
        "--turns-per-page", type=int, default=3,
        help="messages per slide (default: 3)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="show the candidate cells ranked, without writing anything",
    )
    parser.add_argument(
        "--run-name",
        help="analysis run directory to write into "
             "(default: metrics_balanced / metrics_full)",
    )
    args = parser.parse_args()

    selection = select(EXPERIMENTS_DIR, expected_turns=args.turns)
    if not args.full:
        selection = balance(selection)

    if not selection.replicates:
        print("Nothing to build: no runs passed selection.")
        return 1

    if args.list:
        ranked = pick_example(load_cells(selection))
        print(RULE)
        print(" CÉLULAS CANDIDATAS (melhores primeiro)")
        print(RULE)
        print(f" {'tema':20} {'par':9} {'rep':>3} {'escalada':>9} {'Δ':>7}")
        for example in ranked:
            print(
                f" {example.cell.topic:20} {example.cell.pair_id:9} "
                f"{example.cell.replicate:>3} {example.escalation:>+9} "
                f"{example.delta:>+7.2f}"
            )
        print(RULE)
        print(" escalada = nota do último turno menos a do primeiro, no controle")
        return 0

    run_name = args.run_name or (
        "metrics_full" if args.full else "metrics_balanced"
    )
    out_dir = ANALYSIS_DIR / "runs" / run_name / "examples"

    result = build_showcase(
        selection, out_dir,
        topic=args.topic, pair_id=args.pair,
        turns_per_page=args.turns_per_page,
    )

    if not result["pages"]:
        print("No cell matched the requested topic/pair.")
        return 1

    example = result["example"]
    print(RULE)
    print(" EXEMPLO TRABALHADO")
    print(RULE)
    print(f"  célula      : {example.cell.topic} · {example.cell.pair_id} "
          f"· réplica {example.cell.replicate}")
    print(f"  controle    : {example.cell.control.mean_hostility:.2f}")
    print(f"  tratamento  : {example.cell.treatment.mean_hostility:.2f}")
    print(f"  Δ           : {example.delta:+.2f}")
    print(f"  escalada    : {example.escalation:+d} (controle, turno 1 → 8)")
    print()
    print(f"  páginas     : {len(result['pages'])}")
    for page in result["pages"]:
        print(f"    {page.name}")
    print(f"  markdown    : exemplo.md")
    print(f"  saída       : {out_dir}")
    print(RULE)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
