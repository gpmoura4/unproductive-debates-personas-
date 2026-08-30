"""Run a pilot debate: control and treatment over the same topic and pair.

Produces real experiment data. Start small — the defaults are a 4-turn debate
in each condition, which is the "1 pair, 3-4 turns" pilot from the design doc,
not the full 12-turn run.

Run (from the repo root or from debate_simulation/):
    uv run python debate_simulation/scripts/run_debate.py
    uv run python debate_simulation/scripts/run_debate.py --turns 6
    uv run python debate_simulation/scripts/run_debate.py --condition treatment
    uv run python debate_simulation/scripts/run_debate.py --topic "Abortion"

Exit code 0 if every requested debate completed, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_SRC = _PROJECT_DIR / "src"


def _reexec_in_project_venv() -> None:
    """Re-run under debate_simulation/.venv when dependencies are missing.

    Same guard as smoke_test.py: an unrelated active virtualenv would
    otherwise fail with an opaque ModuleNotFoundError.
    """
    venv_python = _PROJECT_DIR / ".venv" / "bin" / "python"
    already_correct = Path(sys.prefix).resolve() == (_PROJECT_DIR / ".venv").resolve()
    if already_correct or not venv_python.is_file():
        return
    if os.environ.get("_DEBATE_RUN_REEXEC") == "1":
        return

    env = dict(os.environ, _DEBATE_RUN_REEXEC="1")
    env.pop("VIRTUAL_ENV", None)
    os.execve(str(venv_python), [str(venv_python), __file__, *sys.argv[1:]], env)


try:
    import openai  # noqa: F401
    import yaml  # noqa: F401
except ModuleNotFoundError:
    _reexec_in_project_venv()
    raise

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config.loader import ConfigError, load_profile  # noqa: E402
from debate.loop import CONTROL, TREATMENT, DebateLoop, write_transcript  # noqa: E402
from debater.debater import Debater  # noqa: E402
from llm.client import LLMCallError, LLMClient  # noqa: E402
from moderator.logger import (  # noqa: E402
    ModerationLogger,
    build_experiment_id,
    build_manifest,
)
from moderator.moderator import D5Moderator  # noqa: E402
from moderator.prompt import DEFAULT_SYSTEM_PROMPT_PATH  # noqa: E402

DEFAULT_TOPIC = "Gun Ownership"
DEFAULT_PAIR_ID = "pair-00"
DEFAULT_TURNS = 4

PREVIEW_CHARS = 300


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a pilot debate in one or both conditions."
    )
    parser.add_argument("--profile", default=None, help="Model profile (default: smoke_test).")
    parser.add_argument("--topic", default=DEFAULT_TOPIC)
    parser.add_argument("--pair", default=DEFAULT_PAIR_ID, help="Pair id, e.g. pair-00.")
    parser.add_argument(
        "--persona-index",
        type=int,
        default=0,
        help="Index of the persona to use from each pole (default: 0).",
    )
    parser.add_argument("--turns", type=int, default=DEFAULT_TURNS)
    parser.add_argument(
        "--condition",
        choices=[CONTROL, TREATMENT, "both"],
        default="both",
        help="Which condition(s) to run (default: both).",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _print_turn(result) -> None:
    """Live progress: what was proposed, what was published."""
    header = f"  Turn {result.turn} [{result.persona_id}]"
    if result.moderated:
        header += f"  hostility={result.hostility_level}"
        if result.was_reformulated:
            header += "  REFORMULATED"
    elif result.moderation_error:
        header += "  MODERATION FAILED — candidate published"
    print(header)

    if result.was_reformulated:
        print(f"    candidate : {result.candidate[:PREVIEW_CHARS]}")
        print(f"    published : {result.published_text[:PREVIEW_CHARS]}")
    else:
        print(f"    {result.published_text[:PREVIEW_CHARS]}")
    if result.consistency_warning:
        print(f"    ! {result.consistency_warning}")


def run_condition(args, profile, condition: str) -> bool:
    """Run one debate. Returns True when it completed all planned turns."""
    print(f"\n{'=' * 70}\n{condition.upper()} — {args.topic} · {args.pair}\n{'=' * 70}")

    experiment_id = build_experiment_id(args.topic, args.pair, condition)
    manifest = build_manifest(
        experiment_id=experiment_id,
        topic=args.topic,
        pair_id=args.pair,
        condition=condition,
        profile=profile,
        persona_1_index=args.persona_index,
        persona_2_index=args.persona_index,
        moderator_prompt_path=DEFAULT_SYSTEM_PROMPT_PATH,
        planned_turns=args.turns,
        seed=args.seed,
    )

    logger = ModerationLogger(experiment_id, manifest)
    logger.write_manifest()

    debater_client = LLMClient(profile.debater)
    debaters = {
        "persona_1": Debater(
            client=debater_client,
            persona_id="persona_1",
            topic=args.topic,
            pole="left",
            persona_index=args.persona_index,
        ),
        "persona_2": Debater(
            client=debater_client,
            persona_id="persona_2",
            topic=args.topic,
            pole="right",
            persona_index=args.persona_index,
        ),
    }

    moderator = (
        D5Moderator(client=LLMClient(profile.moderator), logger=logger)
        if condition == TREATMENT
        else None
    )

    loop = DebateLoop(
        experiment_id=experiment_id,
        topic=args.topic,
        condition=condition,
        debaters=debaters,
        moderator=moderator,
        logger=logger,
    )

    result = loop.run(planned_turns=args.turns, on_turn=_print_turn)
    transcript_path = write_transcript(result, logger.experiment_dir)

    print(f"\n  turns completed : {len(result.turns)}/{args.turns}")
    if condition == TREATMENT:
        print(f"  interventions   : {result.intervention_count}")
        if result.unmoderated_turns:
            print(f"  UNMODERATED     : turns {result.unmoderated_turns}")
    if not result.completed:
        print(f"  STOPPED         : {result.stopped_reason}")
    print(f"  transcript      : {transcript_path}")

    return result.completed


def main() -> int:
    args = _parse_args()

    try:
        profile = load_profile(args.profile)
    except ConfigError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    print(f"Profile   : {profile.name}")
    print(f"Debater   : {profile.debater.model}")
    print(f"Moderator : {profile.moderator.model}")
    print(f"Turns     : {args.turns}   Seed: {args.seed}")

    conditions = (
        [CONTROL, TREATMENT] if args.condition == "both" else [args.condition]
    )

    results = {}
    for condition in conditions:
        try:
            results[condition] = run_condition(args, profile, condition)
        except (LLMCallError, ConfigError) as e:
            print(f"\n[ERROR] {condition}: {e}", file=sys.stderr)
            results[condition] = False

    print(f"\n{'=' * 70}")
    for condition, completed in results.items():
        print(f"  {'OK  ' if completed else 'FAIL'}  {condition}")
    print("=" * 70)

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
