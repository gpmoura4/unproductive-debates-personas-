"""Tests for moderator prompt assembly.

The blinding assertions here are the structural guarantee behind the
moderator's ideological neutrality: if a pole label ever reaches the user
message, the moderator could apply different standards to each side and the
experiment's central claim would not hold.
"""

from __future__ import annotations

import re

import pytest

from moderator.prompt import (
    DEFAULT_SYSTEM_PROMPT_PATH,
    EMPTY_HISTORY_TEXT,
    build_user_message,
    load_system_prompt,
    prompt_sha256,
)
from moderator.schema import ModerationRequest, PublishedMessage


def request_with(history, candidate="Candidate text.", persona_id="persona_2"):
    return ModerationRequest(
        topic="Gun Ownership",
        persona_id=persona_id,
        history=history,
        candidate=candidate,
    )


# --- history rendering -----------------------------------------------------


def test_renders_history_in_turn_order():
    message = build_user_message(
        request_with(
            [
                PublishedMessage(turn=1, persona_id="persona_1", text="First."),
                PublishedMessage(turn=2, persona_id="persona_2", text="Second."),
                PublishedMessage(turn=3, persona_id="persona_1", text="Third."),
            ]
        )
    )

    assert message.index("First.") < message.index("Second.") < message.index("Third.")
    assert "[Turn 1 — Persona 1]: First." in message
    assert "[Turn 2 — Persona 2]: Second." in message


def test_reorders_history_passed_out_of_sequence():
    """Turn order is the moderator's only cue to how the debate escalated."""
    message = build_user_message(
        request_with(
            [
                PublishedMessage(turn=3, persona_id="persona_1", text="Third."),
                PublishedMessage(turn=1, persona_id="persona_1", text="First."),
                PublishedMessage(turn=2, persona_id="persona_2", text="Second."),
            ]
        )
    )

    assert message.index("First.") < message.index("Second.") < message.index("Third.")


def test_empty_history_uses_the_exact_placeholder():
    message = build_user_message(request_with([]))

    assert EMPTY_HISTORY_TEXT in message
    assert EMPTY_HISTORY_TEXT == (
        "(no messages published yet — this is the opening message of the debate)"
    )


def test_layout_matches_the_prompts_expected_sections():
    message = build_user_message(
        request_with(
            [PublishedMessage(turn=1, persona_id="persona_1", text="Opening.")],
            candidate="My reply.",
        )
    )

    assert message.startswith("TOPIC: Gun Ownership")
    for section in ("HISTORY:", "PERSONA: Persona 2", "CANDIDATE:"):
        assert section in message
    assert message.index("HISTORY:") < message.index("PERSONA:")
    assert message.index("PERSONA:") < message.index("CANDIDATE:")
    assert message.rstrip().endswith("My reply.")


def test_rejects_unknown_persona_id():
    with pytest.raises(ValueError, match="Unknown persona_id"):
        build_user_message(request_with([], persona_id="persona_3"))


def test_rejects_unknown_persona_id_in_history():
    with pytest.raises(ValueError, match="Unknown persona_id"):
        build_user_message(
            request_with([PublishedMessage(turn=1, persona_id="left_1", text="Hi.")])
        )


# --- blinding --------------------------------------------------------------

# Terms that would reveal, or let the moderator infer, which pole is which.
BLINDED_TERMS = ("left", "right", "pole", "political", "lean", "esquerda", "direita")


def test_user_message_carries_no_political_orientation_label():
    """The moderator must not be able to tell which pole is which."""
    message = build_user_message(
        request_with(
            [
                PublishedMessage(turn=1, persona_id="persona_1", text="Opening."),
                PublishedMessage(turn=2, persona_id="persona_2", text="Reply."),
            ]
        )
    )

    lowered = message.lower()
    for term in BLINDED_TERMS:
        assert not re.search(rf"\b{term}\b", lowered), (
            f"Blinded term {term!r} leaked into the moderator's user message"
        )


def test_personas_are_identified_only_by_debate_seat():
    message = build_user_message(
        request_with(
            [PublishedMessage(turn=1, persona_id="persona_1", text="Opening.")]
        )
    )

    assert "Persona 1" in message
    assert "Persona 2" in message  # the candidate's author
    assert "polo_esquerda" not in message
    assert "matraix" not in message.lower()


def test_blinding_holds_for_the_empty_history_case():
    message = build_user_message(request_with([], persona_id="persona_1"))

    lowered = message.lower()
    for term in BLINDED_TERMS:
        assert not re.search(rf"\b{term}\b", lowered)


def test_debater_text_is_passed_through_verbatim():
    """Blinding constrains our framing, not what the personas actually said.

    A debater may well say "the right" mid-argument; censoring that would
    corrupt the message the moderator has to score.
    """
    message = build_user_message(
        request_with(
            [PublishedMessage(turn=1, persona_id="persona_1", text="The right is wrong.")],
            candidate="You people on the left never listen.",
        )
    )

    assert "The right is wrong." in message
    assert "You people on the left never listen." in message


# --- system prompt ---------------------------------------------------------


def test_system_prompt_loads_verbatim():
    prompt = load_system_prompt()

    assert "D5 Participatory Moderator" in prompt
    assert "HOSTILITY SCALE" in prompt
    # Loaded unmodified, so its digest describes what was actually sent.
    assert prompt == DEFAULT_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def test_system_prompt_instructs_ideological_neutrality():
    prompt = load_system_prompt().lower()

    assert "ideologically neutral" in prompt
    assert "must not infer" in prompt


def test_prompt_digest_is_stable_and_well_formed():
    digest = prompt_sha256()

    assert len(digest) == 64
    assert digest == prompt_sha256()


def test_missing_prompt_file_raises(tmp_path):
    missing = tmp_path / "absent.txt"

    with pytest.raises(FileNotFoundError):
        load_system_prompt(missing)
    with pytest.raises(FileNotFoundError):
        prompt_sha256(missing)
