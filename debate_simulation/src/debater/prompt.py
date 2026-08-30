"""Debater prompt assembly: Layer 1 + Layer 2 into one system prompt.

Layer 1 is the persona's ideological identity, generated per persona by
`scripts/00_generate_persona_prompts.py`. Layer 2 is the shared behavioral
layer (`prompts/debate behavior/debate behavior.txt`) that makes the debate
unproductive. Both are read verbatim and concatenated — neither is rewritten
here, so their digests describe exactly what was sent.

Blinding invariant: the composed prompt carries a persona's own attributes but
never names its pole, and the debate history identifies the opponent only as
"Persona 1" / "Persona 2". A debater knows what it believes, not which side of
the study it was sampled into, and not which side its opponent is on.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from moderator.schema import PublishedMessage

# Anchored to this file (src/debater/prompt.py -> debate_simulation/) so the
# defaults resolve the same from the repo root or from debate_simulation/.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_BEHAVIOR_PROMPT_PATH = (
    _PROJECT_ROOT / "prompts" / "debate behavior" / "debate behavior.txt"
)

PERSONAS_DIR = _PROJECT_ROOT / "outputs" / "prompts" / "personas"

POLE_DIRECTORIES = {"left": "polo_esquerda", "right": "polo_direita"}

# Debate-seat labels, matching the moderator's. They encode turn order, not
# ideology.
PERSONA_LABELS = {"persona_1": "Persona 1", "persona_2": "Persona 2"}

OPENING_INSTRUCTION = (
    "You are opening the debate. State your position on the topic in your own "
    "voice, following your behavioral rules."
)

REPLY_INSTRUCTION = (
    "Write your next message in the debate, replying to what your opponent "
    "just said. Follow your behavioral rules. Output only the message itself "
    "— no quotation marks, no name prefix, no stage directions."
)

EMPTY_HISTORY_TEXT = (
    "(no messages published yet — this is the opening message of the debate)"
)


def persona_prompt_path(pole: str, persona_index: int) -> Path:
    """Path to one persona's Layer 1 prompt, by pole and index."""
    directory = POLE_DIRECTORIES.get(pole)
    if directory is None:
        raise ValueError(
            f"Unknown pole {pole!r}; expected one of {sorted(POLE_DIRECTORIES)}."
        )
    return PERSONAS_DIR / directory / f"persona_{persona_index:02d}.txt"


def _read_verbatim(path: Path, label: str) -> str:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found at: {path}")
    return path.read_text(encoding="utf-8")


def load_persona_prompt(pole: str, persona_index: int) -> str:
    """Layer 1 for one persona, read verbatim."""
    return _read_verbatim(
        persona_prompt_path(pole, persona_index),
        f"Persona prompt (pole={pole}, index={persona_index})",
    )


def load_behavior_prompt(path: Path = DEFAULT_BEHAVIOR_PROMPT_PATH) -> str:
    """Layer 2, shared by both poles, read verbatim."""
    return _read_verbatim(path, "Behavior prompt")


def build_system_prompt(
    persona_prompt: str, behavior_prompt: str, topic: str
) -> str:
    """Compose one debater's system prompt.

    Order matters: Layer 2 opens by referring to "your ideological identity
    defined above (Layer 1)", so the persona must come first. The topic is
    stated last, since it scopes both layers.
    """
    return (
        f"{persona_prompt.rstrip()}\n\n"
        f"{behavior_prompt.rstrip()}\n\n"
        "---\n\n"
        f"### DEBATE TOPIC\n\nThe topic under debate is: {topic}"
    )


def prompt_sha256(text: str) -> str:
    """Digest of a composed prompt, for recording which text produced a run."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _persona_label(persona_id: str) -> str:
    try:
        return PERSONA_LABELS[persona_id]
    except KeyError:
        raise ValueError(
            f"Unknown persona_id {persona_id!r}; expected one of "
            f"{sorted(PERSONA_LABELS)}"
        ) from None


def build_user_message(
    history: list[PublishedMessage], speaker_id: str
) -> str:
    """Render the published transcript plus the instruction for this turn.

    The history is what was actually published — the reformulated text when the
    moderator intervened. That is what closes the D5 loop: a debater replies to
    what the opponent was allowed to say, not to what they tried to say.

    Messages are labelled YOU / OPPONENT rather than by seat, so the model does
    not have to work out which side it is on.
    """
    _persona_label(speaker_id)  # validate the speaker before rendering

    lines = ["DEBATE SO FAR:"]

    if history:
        for message in sorted(history, key=lambda m: m.turn):
            who = "YOU" if message.persona_id == speaker_id else "OPPONENT"
            lines.append(f"[Turn {message.turn} — {who}]: {message.text}")
    else:
        lines.append(EMPTY_HISTORY_TEXT)

    instruction = OPENING_INSTRUCTION if not history else REPLY_INSTRUCTION
    lines += ["", instruction]

    return "\n".join(lines)
