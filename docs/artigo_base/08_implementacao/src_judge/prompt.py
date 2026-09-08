"""Judge prompt assembly.

Loads `prompts/debate judge/debate judge.txt` verbatim as the system prompt
and renders a `JudgementRequest` into the user message (TOPIC / CONTEXT /
PERSONA / MESSAGE).

Blinding invariant, as for the moderator: debaters are identified only as
"Persona 1" and "Persona 2", never by pole. The judge must also not learn
which condition produced the message — a judge told that a message had been
reformulated would be scoring the intervention rather than the text.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from judge.schema import JudgementRequest

# Anchored to this file (src/judge/prompt.py -> debate_simulation/).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_SYSTEM_PROMPT_PATH = (
    _PROJECT_ROOT / "prompts" / "debate judge" / "debate judge.txt"
)

PERSONA_LABELS = {"persona_1": "Persona 1", "persona_2": "Persona 2"}

EMPTY_CONTEXT_TEXT = "(none — this is the opening message of the debate)"


def load_system_prompt(path: Path = DEFAULT_SYSTEM_PROMPT_PATH) -> str:
    """Read the judge system prompt verbatim."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Judge system prompt not found at: {path.resolve()}")
    return path.read_text(encoding="utf-8")


def prompt_sha256(path: Path = DEFAULT_SYSTEM_PROMPT_PATH) -> str:
    """SHA-256 of the prompt file, for recording prompt version."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Judge system prompt not found at: {path.resolve()}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _persona_label(persona_id: str) -> str:
    try:
        return PERSONA_LABELS[persona_id]
    except KeyError:
        raise ValueError(
            f"Unknown persona_id {persona_id!r}; expected one of "
            f"{sorted(PERSONA_LABELS)}"
        ) from None


def build_user_message(request: JudgementRequest) -> str:
    """Render one message to be scored, with its preceding context.

    Context is rendered in turn order and never includes the message itself —
    the judge scores exactly one message, and including it twice would let the
    context inflate its own score.
    """
    lines = [f"TOPIC: {request.topic}", "", "CONTEXT:"]

    context = [m for m in request.context if m.turn < request.turn]
    if context:
        for message in sorted(context, key=lambda m: m.turn):
            label = _persona_label(message.persona_id)
            lines.append(f"[Turn {message.turn} — {label}]: {message.text}")
    else:
        lines.append(EMPTY_CONTEXT_TEXT)

    lines += [
        "",
        f"PERSONA: {_persona_label(request.persona_id)}",
        "",
        "MESSAGE:",
        request.message,
    ]

    return "\n".join(lines)