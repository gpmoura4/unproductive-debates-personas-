"""Compute metrics, tables and figures from the selected corpus.

Reads only from disk — no API calls, no cost. Writes under analysis/.

Run (from the repo root or from debate_simulation/):
    uv run python debate_simulation/scripts/compute_metrics.py
    uv run python debate_simulation/scripts/compute_metrics.py --full
    uv run python debate_simulation/scripts/compute_metrics.py --audit-sample 30
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_SRC = _PROJECT_DIR / "src"

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from analysis.metrics import compute_all, load_cells, per_turn_table  # noqa: E402
from analysis.report import write_report  # noqa: E402
from analysis.selection import balance, select  # noqa: E402

EXPERIMENTS_DIR = _PROJECT_DIR / "experiments"
ANALYSIS_DIR = _PROJECT_DIR / "analysis"

RULE = "=" * 78


def write_rows(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_audit_sample(selection, size: int, seed: int) -> list[dict]:
    """Candidate/reformulation pairs for manual annotation.

    Sampled with a fixed seed so the same corpus yields the same sample — the
    annotation has to be traceable to specific turns, not to "thirty pairs we
    happened to draw".
    """
    import json as _json

    pairs: list[dict] = []
    for replicate in selection.replicates:
        run = replicate.treatment
        moderation_dir = run.path / "moderation"
        if not moderation_dir.is_dir():
            continue
        for path in sorted(moderation_dir.glob("turn_*.json")):
            try:
                record = _json.loads(path.read_text(encoding="utf-8"))
            except (_json.JSONDecodeError, OSError):
                continue
            resolution = record.get("resolution", {})
            if not resolution.get("was_reformulated"):
                continue
            moderation = record.get("moderation", {})
            pairs.append(
                {
                    "experiment_id": record.get("experiment_id"),
                    "topic": record.get("topic"),
                    "pair_id": replicate.pair_id,
                    "replicate": replicate.index,
                    "turn": record.get("turn"),
                    "persona_id": record.get("persona_id"),
                    "moderator_hostility": moderation.get("hostility_level"),
                    "candidate": record.get("input", {}).get("candidate", ""),
                    "reformulation": resolution.get("published_text", ""),
                    "argument_preserved_claim": moderation.get("argument_preserved", ""),
                    # Columns for the human annotator to fill in.
                    "posicao_preservada": "",
                    "hostilidade_reduzida": "",
                    "observacoes": "",
                }
            )

    rng = random.Random(seed)
    rng.shuffle(pairs)
    return pairs[:size]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--turns", type=int, default=8,
        help="turn count the analysis expects (default: 8)",
    )
    parser.add_argument(
        "--full", action="store_true",
        help="use the complete corpus instead of the balanced design",
    )
    parser.add_argument(
        "--name",
        help="output directory under analysis/runs/ (default: metrics_<design>)",
    )
    parser.add_argument(
        "--audit-sample", type=int, default=30,
        help="candidate/reformulation pairs to sample for manual audit (0 to skip)",
    )
    parser.add_argument(
        "--audit-seed", type=int, default=42,
        help="seed for the audit sample, so it is reproducible",
    )
    args = parser.parse_args()

    selection = select(EXPERIMENTS_DIR, expected_turns=args.turns)
    if not args.full:
        selection = balance(selection)

    if not selection.replicates:
        print("Nothing to compute: no runs passed selection.")
        print("Check `show_selection.py --excluded` to see why.")
        return 1

    design = "completo" if args.full else "balanceado"
    out_dir = ANALYSIS_DIR / "runs" / (
        args.name or f"metrics_{'full' if args.full else 'balanced'}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics = compute_all(selection)
    (out_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    created = write_report(metrics, out_dir)

    # Long-format export: one row per published message, for any analysis the
    # canned tables do not cover.
    rows = per_turn_table(load_cells(selection))
    write_rows(rows, out_dir / "tables" / "per_turn.csv")

    sample = []
    if args.audit_sample:
        sample = build_audit_sample(selection, args.audit_sample, args.audit_seed)
        write_rows(sample, out_dir / "amostra_auditoria.csv")

    effect = metrics["main_effect"]
    corpus = metrics["corpus"]

    print(RULE)
    print(f" MÉTRICAS — desenho {design}")
    print(RULE)
    print(f"  células     : {corpus['cells']}")
    print(f"  réplicas    : {corpus['replicates']}")
    print(f"  debates     : {corpus['debates']}")
    print()
    print(f"  controle    : {effect['control']['mean']:.3f}")
    print(f"  tratamento  : {effect['treatment']['mean']:.3f}")
    print(f"  Δ           : {effect['delta']['mean']:.3f}  "
          f"(dp {effect['delta']['sd']:.3f})")
    print(f"  células Δ<0 : {effect['cells_favouring_treatment']}"
          f"/{effect['delta']['n']}")
    print()
    print(f"  saída       : {out_dir}")
    print(f"  arquivos    : metrics.json, report.md, "
          f"{len(created) - 1} tabelas/figuras")
    if sample:
        print(f"  auditoria   : amostra_auditoria.csv ({len(sample)} pares)")
    print(RULE)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
