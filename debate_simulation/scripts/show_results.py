"""Read back an experiment run in human-readable form.

Reads only from disk — no API calls, no cost. Use it after run_debate.py to
inspect what happened at each stage: what the debaters proposed, what the
moderator did with it, and how the judge scored what was published.

Run (from the repo root or from debate_simulation/):
    uv run python debate_simulation/scripts/show_results.py            # list runs
    uv run python debate_simulation/scripts/show_results.py --last     # newest run
    uv run python debate_simulation/scripts/show_results.py <experiment_id>
    uv run python debate_simulation/scripts/show_results.py --compare  # control vs treatment
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_SRC = _PROJECT_DIR / "src"

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

EXPERIMENTS_DIR = _PROJECT_DIR / "experiments"

RULE = "=" * 78
THIN = "-" * 78


def _wrap(text: str, indent: str = "    ", width: int = 74) -> str:
    """Wrap text to the terminal, preserving the debaters' own line breaks."""
    paragraphs = text.split("\n")
    wrapped = []
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
        wrapped.extend(
            textwrap.wrap(paragraph, width=width) or [""]
        )
    return "\n".join(indent + line for line in wrapped)


def _load(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_runs() -> list[Path]:
    if not EXPERIMENTS_DIR.is_dir():
        return []
    return sorted(p for p in EXPERIMENTS_DIR.iterdir() if p.is_dir())


def _judgements(run_dir: Path) -> dict[int, dict]:
    """Judge scores by turn, when the judging pass ran."""
    judgements_dir = run_dir / "judgements"
    if not judgements_dir.is_dir():
        return {}

    by_turn: dict[int, dict] = {}
    for path in sorted(judgements_dir.glob("turn_*.json")):
        if "_FAILED" in path.stem:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        by_turn[payload["turn"]] = payload
    return by_turn


def _moderation(run_dir: Path) -> dict[int, dict]:
    """Moderation records by turn, for the full justification text."""
    moderation_dir = run_dir / "moderation"
    if not moderation_dir.is_dir():
        return {}

    by_turn: dict[int, dict] = {}
    for path in sorted(moderation_dir.glob("turn_*.json")):
        if "_FAILED" in path.stem:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        by_turn[payload["turn"]] = payload
    return by_turn


def show_run(run_dir: Path, full: bool = False) -> None:
    manifest = _load(run_dir / "manifest.json")
    transcript = _load(run_dir / "transcript.json")

    if manifest is None:
        print(f"[!] {run_dir.name}: no manifest.json")
        return

    print(f"\n{RULE}")
    print(f"{manifest['condition'].upper()}  ·  {manifest['topic']}  ·  {manifest['pair_id']}")
    print(f"{run_dir.name}")
    print(RULE)

    models = manifest.get("models", {})
    print(f"  debaters  : {models.get('debaters', {}).get('model')}")
    if models.get("moderator"):
        print(f"  moderator : {models['moderator'].get('model')}")
    if models.get("judge"):
        print(f"  judge     : {models['judge'].get('model')}")

    personas = manifest.get("personas", {})
    for seat in ("persona_1", "persona_2"):
        entry = personas.get(seat, {})
        print(
            f"  {seat} : pole={entry.get('pole')} "
            f"index={entry.get('persona_index')} "
            f"source={entry.get('matraix_source')}/{entry.get('matraix_id')}"
        )

    if transcript is None:
        print("\n  (no transcript.json — the debate did not produce one)")
        return

    judgements = _judgements(run_dir)
    moderation = _moderation(run_dir)

    print(f"\n  turns={transcript['turn_count']}  "
          f"interventions={transcript['intervention_count']}  "
          f"completed={transcript['completed']}")
    if transcript.get("unmoderated_turns"):
        print(f"  UNMODERATED TURNS: {transcript['unmoderated_turns']}")
    if transcript.get("stopped_reason"):
        print(f"  stopped: {transcript['stopped_reason']}")

    for turn in transcript["turns"]:
        n = turn["turn"]
        print(f"\n{THIN}")
        header = f"TURN {n}  [{turn['persona_id']}]"
        if turn.get("moderated"):
            header += f"   moderator: hostility={turn['hostility_level']}"
            if turn["pathologies_detected"]:
                header += f" {turn['pathologies_detected']}"
        elif turn.get("moderation_error"):
            header += "   MODERATION FAILED"
        print(header)

        if turn["was_reformulated"]:
            print("\n  CANDIDATE (what the debater wrote):")
            print(_wrap(turn["candidate"]))
            print("\n  PUBLISHED (after reformulation):")
            print(_wrap(turn["published_text"]))
        else:
            print("\n  PUBLISHED:")
            print(_wrap(turn["published_text"]))

        record = moderation.get(n)
        if record and full:
            print("\n  moderator's justification:")
            print(_wrap(record["moderation"]["justification"]))
            if record["moderation"].get("argument_preserved"):
                print("\n  argument preserved:")
                print(_wrap(record["moderation"]["argument_preserved"]))

        if turn.get("consistency_warning"):
            print(f"\n  ! {turn['consistency_warning']}")

        judgement = judgements.get(n)
        if judgement:
            summary = judgement["summary"]
            flag = "" if summary["unanimous"] else "  <- judge disagreed with itself"
            print(
                f"\n  JUDGE: median={summary['median']}  "
                f"runs={summary['scores']}{flag}"
            )
            if full:
                print(_wrap(judgement["runs"][0]["justification"], indent="         "))

    _print_trajectory(transcript, judgements)


def _print_trajectory(transcript: dict, judgements: dict[int, dict]) -> None:
    """The hostility curve — the thing the experiment is actually measuring."""
    if not judgements:
        print(f"\n{THIN}")
        print("  (no judge scores — re-run with --judge to produce them)")
        return

    print(f"\n{THIN}")
    print("  HOSTILITY TRAJECTORY (judge, median of runs)\n")

    scores = []
    for turn in transcript["turns"]:
        judgement = judgements.get(turn["turn"])
        if judgement is None:
            continue
        median = judgement["summary"]["median"]
        scores.append(median)
        bar = "#" * int(median * 6) if median else ""
        print(f"    turn {turn['turn']:>2} [{turn['persona_id']}]  {median}  {bar}")

    if scores:
        print(f"\n    mean hostility: {sum(scores) / len(scores):.2f}")

    disagreed = [
        t for t, j in judgements.items() if not j["summary"]["unanimous"]
    ]
    if disagreed:
        print(f"    judge self-disagreement on turns: {sorted(disagreed)}")


def compare() -> None:
    """Control vs treatment: the main effect, side by side."""
    runs = list_runs()
    by_condition: dict[str, Path] = {}
    for run_dir in runs:
        manifest = _load(run_dir / "manifest.json")
        if manifest:
            by_condition[manifest["condition"]] = run_dir  # newest wins

    if len(by_condition) < 2:
        print("Need one control run and one treatment run to compare.")
        print(f"Found: {sorted(by_condition)}")
        return

    print(f"\n{RULE}")
    print("CONTROL vs TREATMENT — mean hostility per turn (judge medians)")
    print(RULE)

    for condition in ("control", "treatment"):
        run_dir = by_condition.get(condition)
        if run_dir is None:
            continue
        transcript = _load(run_dir / "transcript.json")
        judgements = _judgements(run_dir)
        if not transcript:
            continue

        scores = [
            judgements[t["turn"]]["summary"]["median"]
            for t in transcript["turns"]
            if t["turn"] in judgements
        ]
        line = f"  {condition:<10}"
        if scores:
            mean = sum(scores) / len(scores)
            line += f"  mean={mean:.2f}  per-turn={scores}"
        else:
            line += "  (not judged)"
        line += f"  interventions={transcript['intervention_count']}"
        print(line)

    print(
        "\n  Note: the judge scores PUBLISHED text. In treatment that is the\n"
        "  reformulation where the moderator intervened — which is the point."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect experiment results.")
    parser.add_argument("experiment_id", nargs="?", help="Run to show.")
    parser.add_argument("--last", action="store_true", help="Show the newest run.")
    parser.add_argument("--all", action="store_true", help="Show every run.")
    parser.add_argument(
        "--compare", action="store_true", help="Control vs treatment summary."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include moderator and judge justifications.",
    )
    args = parser.parse_args()

    runs = list_runs()
    if not runs:
        print(f"No runs found in {EXPERIMENTS_DIR}")
        print("Run scripts/run_debate.py first.")
        return 1

    if args.compare:
        compare()
        return 0

    if args.experiment_id:
        target = EXPERIMENTS_DIR / args.experiment_id
        if not target.is_dir():
            print(f"No such run: {args.experiment_id}")
            return 1
        show_run(target, full=args.full)
        return 0

    if args.last:
        show_run(runs[-1], full=args.full)
        return 0

    if args.all:
        for run_dir in runs:
            show_run(run_dir, full=args.full)
        return 0

    print(f"\n{len(runs)} run(s) in {EXPERIMENTS_DIR}:\n")
    for run_dir in runs:
        manifest = _load(run_dir / "manifest.json")
        transcript = _load(run_dir / "transcript.json")
        judged = "judged" if (run_dir / "judgements").is_dir() else "not judged"
        turns = transcript["turn_count"] if transcript else 0
        condition = manifest["condition"] if manifest else "?"
        print(f"  {run_dir.name}")
        print(f"      {condition}  ·  {turns} turns  ·  {judged}")

    print("\nShow one with:")
    print("  uv run python debate_simulation/scripts/show_results.py --last")
    print("  uv run python debate_simulation/scripts/show_results.py --compare")
    return 0


if __name__ == "__main__":
    sys.exit(main())