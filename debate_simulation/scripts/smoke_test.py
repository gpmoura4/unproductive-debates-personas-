"""End-to-end smoke test of the LLM plumbing (no debate logic involved).

Validates, before any debate/judge module exists, that:
  1. the `smoke_test` profile loads,
  2. all three roles can make a real call and return output,
  3. latency and token usage are captured,
  4. OpenRouter authentication works.

Deliberately independent of the debate loop, judge and persona selection: it
sends hardcoded minimal payloads, so a failure here is a plumbing failure.

Run (from the repo root or from debate_simulation/):
    uv run python debate_simulation/scripts/smoke_test.py
    uv run python debate_simulation/scripts/smoke_test.py --profile local

Exit code 0 if all three calls succeed, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_SRC = _PROJECT_DIR / "src"


def _reexec_in_project_venv() -> None:
    """Re-run this script under debate_simulation/.venv when needed.

    The interpreter in use may lack this subproject's dependencies — when an
    unrelated virtualenv is active (a stale VIRTUAL_ENV from another project),
    or when uv resolved a different environment. Rather than fail with an
    opaque ModuleNotFoundError, hand off to the venv that has them.
    """
    venv_python = _PROJECT_DIR / ".venv" / "bin" / "python"
    already_correct = Path(sys.prefix).resolve() == (_PROJECT_DIR / ".venv").resolve()
    if already_correct or not venv_python.is_file():
        return
    if os.environ.get("_DEBATE_SMOKE_REEXEC") == "1":
        return  # guard against an exec loop

    env = dict(os.environ, _DEBATE_SMOKE_REEXEC="1")
    env.pop("VIRTUAL_ENV", None)  # stale value would shadow the target venv
    os.execve(str(venv_python), [str(venv_python), __file__, *sys.argv[1:]], env)


try:
    import openai  # noqa: F401  — probe: present only in the right environment
    import yaml  # noqa: F401
except ModuleNotFoundError:
    _reexec_in_project_venv()
    raise

# Make the subproject's packages importable however this script is invoked:
# from the repo root, uv resolves the root environment, which does not have
# debate-simulation installed, so src/ is added explicitly.
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config.loader import ConfigError, ModelConfig, available_profiles, load_profile  # noqa: E402
from llm.client import LLMCallError, LLMClient  # noqa: E402

SYSTEM_PROMPT = "You are a test assistant. Respond in one short sentence."

RESPONSE_PREVIEW_CHARS = 200


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that all three roles can reach their configured models."
    )
    parser.add_argument(
        "--profile",
        default=None,
        help=(
            "Profile to test (default: smoke_test). Overrides DEBATE_PROFILE "
            "and the config's default_profile."
        ),
    )
    return parser.parse_args()


def _check_role(role_name: str, model_config: ModelConfig) -> bool:
    """Call one role's model. Returns True on success."""
    print(f"\n--- {role_name.upper()} ---")
    try:
        client = LLMClient(model_config)
        text, meta = client.call(
            system_prompt=SYSTEM_PROMPT,
            user_message=(
                f"Confirm you are the {role_name} model and state your name."
            ),
        )
    except LLMCallError as e:
        print(f"FAILED  : {e}")
        return False

    print(f"Response: {text.strip()[:RESPONSE_PREVIEW_CHARS]}")
    print(f"Latency : {meta['latency_ms']} ms")
    print(f"Usage   : {meta.get('usage')}")
    if meta["attempts"] > 1:
        print(f"Attempts: {meta['attempts']} (transient failures were retried)")
    return True


def main() -> int:
    args = _parse_args()

    try:
        profile = load_profile(args.profile or "smoke_test")
    except ConfigError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    print(f"Profile  : {profile.name}")
    print(f"Debater  : {profile.debater.model}  ({profile.debater.provider})")
    print(f"Moderator: {profile.moderator.model}  ({profile.moderator.provider})")
    print(f"Judge    : {profile.judge.model}  ({profile.judge.provider})")

    results = {
        role_name: _check_role(role_name, model_config)
        for role_name, model_config in (
            ("debater", profile.debater),
            ("moderator", profile.moderator),
            ("judge", profile.judge),
        )
    }

    passed = sum(results.values())
    total = len(results)

    print("\n" + "=" * 46)
    for role_name, succeeded in results.items():
        print(f"  {'PASS' if succeeded else 'FAIL'}  {role_name}")
    print("=" * 46)

    if passed == total:
        print(f"SMOKE TEST PASSED — {passed}/{total} roles reachable.")
        print("The pipeline is wired correctly; you can proceed.")
        return 0

    print(f"SMOKE TEST FAILED — {passed}/{total} roles reachable.")
    if profile.name in {"local", "hybrid"}:
        print("For Ollama roles, check that the server is running: ollama serve")
    print(f"Available profiles: {', '.join(available_profiles())}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
