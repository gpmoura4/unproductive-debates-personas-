"""Moderator prompt assembly.

Loads `prompts/debate moderator D5/debate moderator D5.txt` verbatim as the
system prompt and renders a `ModerationRequest` into the user message
(TOPIC / HISTORY / PERSONA / CANDIDATE).

Blinding invariant: the user message identifies the debaters only as
"Persona 1" and "Persona 2". It must never carry political orientation, pole
labels, or any MatrAIx attribute data — the moderator's ideological
neutrality depends on it being unable to tell which pole is which. Nothing in
this module reads persona attributes or metadata, which is what keeps that
invariant structural rather than a matter of care.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from moderator.schema import ModerationRequest

# Anchored to this file's location (src/moderator/prompt.py -> debate_simulation/)
# so the default resolves the same whether a caller runs from the repo root or
# from debate_simulation/. The path contains spaces; it is only ever handled as
# a Path, never interpolated into a shell command.
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_SYSTEM_PROMPT_PATH = (
    _PACKAGE_ROOT / "prompts" / "debate moderator D5" / "debate moderator D5.txt"
)

# Debate-seat labels shown to the moderator. Deliberately opaque: they encode
# turn order, not ideology.
PERSONA_LABELS = {
    "persona_1": "Persona 1",
    "persona_2": "Persona 2",
}

EMPTY_HISTORY_TEXT = (
    "(no messages published yet — this is the opening message of the debate)"
)


def load_system_prompt(path: Path = DEFAULT_SYSTEM_PROMPT_PATH) -> str:
    """Read the moderator system prompt verbatim.

    The content is returned exactly as stored — no stripping, normalizing or
    reformatting — so that `prompt_sha256` of the same file always describes
    the string actually sent to the model.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Moderator system prompt not found at: {path.resolve()}"
        )
    return path.read_text(encoding="utf-8")


def prompt_sha256(path: Path = DEFAULT_SYSTEM_PROMPT_PATH) -> str:
    """SHA-256 hex digest of the prompt file, for recording prompt version.

    Digests the raw bytes, so it pins the exact file that produced a run.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Moderator system prompt not found at: {path.resolve()}"
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _persona_label(persona_id: str) -> str:
    try:
        return PERSONA_LABELS[persona_id]
    except KeyError:
        raise ValueError(
            f"Unknown persona_id {persona_id!r}; expected one of "
            f"{sorted(PERSONA_LABELS)}"
        ) from None


def build_user_message(request: ModerationRequest) -> str:
    """Render a moderation request as the user message for the moderator.

    Layout matches the prompt's WHAT YOU RECEIVE section:

        TOPIC: ...

        HISTORY:
        [Turn 1 — Persona 1]: ...

        PERSONA: Persona 2

        CANDIDATE:
        ...

    History is rendered in turn order regardless of the order it was passed in.
    """
    lines = [f"TOPIC: {request.topic}", "", "HISTORY:"]

    if request.history:
        for message in sorted(request.history, key=lambda m: m.turn):
            label = _persona_label(message.persona_id)
            lines.append(f"[Turn {message.turn} — {label}]: {message.text}")
    else:
        lines.append(EMPTY_HISTORY_TEXT)

    lines += [
        "",
        f"PERSONA: {_persona_label(request.persona_id)}",
        "",
        "CANDIDATE:",
        request.candidate,
    ]

    return "\n".join(lines)
