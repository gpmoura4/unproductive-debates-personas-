"""Tests for the debating agent — prompt composition and message cleanup."""

from __future__ import annotations

import re

import pytest

from debater.debater import Debater, DebaterError, clean_message
from debater.prompt import (
    EMPTY_HISTORY_TEXT,
    OPENING_INSTRUCTION,
    REPLY_INSTRUCTION,
    build_system_prompt,
    build_user_message,
    load_behavior_prompt,
    load_persona_prompt,
    persona_prompt_path,
)
from moderator.schema import PublishedMessage

from tests.test_moderator import FakeClient

PERSONA_PROMPT = "You are a debate persona.\n\n- stance on guns: Positive"
BEHAVIOR_PROMPT = "## HOW YOU DEBATE\n\nEscalate progressively."


def make_debater(*replies: str, persona_id: str = "persona_1") -> Debater:
    return Debater(
        client=FakeClient(*replies),
        persona_id=persona_id,
        topic="Gun Ownership",
        persona_prompt=PERSONA_PROMPT,
        behavior_prompt=BEHAVIOR_PROMPT,
    )


# --- system prompt ---------------------------------------------------------


def test_system_prompt_puts_persona_before_behavior():
    """Layer 2 refers to the identity 'defined above', so order matters."""
    prompt = build_system_prompt(PERSONA_PROMPT, BEHAVIOR_PROMPT, "Gun Ownership")

    assert prompt.index("debate persona") < prompt.index("HOW YOU DEBATE")
    assert "Gun Ownership" in prompt


def test_system_prompt_keeps_both_layers_verbatim():
    prompt = build_system_prompt(PERSONA_PROMPT, BEHAVIOR_PROMPT, "Abortion")

    assert "stance on guns: Positive" in prompt
    assert "Escalate progressively." in prompt


def test_real_layers_compose():
    """The files on disk actually load and combine."""
    prompt = build_system_prompt(
        load_persona_prompt("left", 0), load_behavior_prompt(), "Gun Ownership"
    )

    assert "Your positioning is defined by the following attributes" in prompt
    assert "RULE SET 1" in prompt
    assert "HARD LIMITS" in prompt


def test_persona_prompt_path_maps_poles():
    assert "polo_esquerda" in str(persona_prompt_path("left", 0))
    assert "polo_direita" in str(persona_prompt_path("right", 3))
    assert persona_prompt_path("right", 3).name == "persona_03.txt"


def test_unknown_pole_raises():
    with pytest.raises(ValueError, match="Unknown pole"):
        persona_prompt_path("centre", 0)


def test_persona_prompt_does_not_name_its_pole():
    """Layer 1 blinding: the persona knows its positions, not its label."""
    for pole in ("left", "right"):
        lowered = load_persona_prompt(pole, 0).lower()
        for term in ("left", "right", "pole", "political lean", "matraix"):
            assert not re.search(rf"\b{re.escape(term)}\b", lowered), (
                f"{term!r} leaked into the {pole} persona prompt"
            )


# --- user message ----------------------------------------------------------


def test_opening_turn_uses_opening_instruction():
    message = build_user_message([], "persona_1")

    assert EMPTY_HISTORY_TEXT in message
    assert OPENING_INSTRUCTION in message
    assert REPLY_INSTRUCTION not in message


def test_later_turn_uses_reply_instruction():
    message = build_user_message(
        [PublishedMessage(turn=1, persona_id="persona_1", text="Opening.")],
        "persona_2",
    )

    assert REPLY_INSTRUCTION in message
    assert OPENING_INSTRUCTION not in message


def test_history_is_labelled_from_the_speakers_view():
    history = [
        PublishedMessage(turn=1, persona_id="persona_1", text="Mine."),
        PublishedMessage(turn=2, persona_id="persona_2", text="Theirs."),
    ]
    message = build_user_message(history, "persona_1")

    assert "[Turn 1 — YOU]: Mine." in message
    assert "[Turn 2 — OPPONENT]: Theirs." in message


def test_the_same_history_flips_for_the_other_speaker():
    history = [PublishedMessage(turn=1, persona_id="persona_1", text="Mine.")]

    assert "YOU]: Mine." in build_user_message(history, "persona_1")
    assert "OPPONENT]: Mine." in build_user_message(history, "persona_2")


def test_history_is_ordered_by_turn():
    history = [
        PublishedMessage(turn=2, persona_id="persona_2", text="Second."),
        PublishedMessage(turn=1, persona_id="persona_1", text="First."),
    ]
    message = build_user_message(history, "persona_1")

    assert message.index("First.") < message.index("Second.")


def test_unknown_speaker_raises():
    with pytest.raises(ValueError, match="Unknown persona_id"):
        build_user_message([], "persona_9")


def test_user_message_carries_no_pole_label():
    history = [PublishedMessage(turn=1, persona_id="persona_2", text="Hi.")]
    lowered = build_user_message(history, "persona_1").lower()

    for term in ("left", "right", "pole", "esquerda", "direita"):
        assert not re.search(rf"\b{term}\b", lowered)


# --- message cleanup -------------------------------------------------------


def test_clean_message_strips_speaker_prefix():
    assert clean_message("YOU: That's absurd.") == "That's absurd."
    assert clean_message("Persona 1: That's absurd.") == "That's absurd."


def test_clean_message_strips_wrapping_quotes():
    assert clean_message('"That\'s absurd."') == "That's absurd."


def test_clean_message_keeps_internal_quotes():
    text = 'Your "data" is propaganda.'
    assert clean_message(text) == text


def test_clean_message_preserves_informal_register():
    """Layer 2 wants lowercase, ellipses and ALL CAPS to survive."""
    text = "lol ok... that's just WRONG."
    assert clean_message(text) == text


def test_clean_message_rejects_empty_output():
    for blank in ("", "   ", '""'):
        with pytest.raises(DebaterError):
            clean_message(blank)


# --- generate_turn ---------------------------------------------------------


def test_generate_turn_returns_cleaned_text_and_metadata():
    debater = make_debater('"Guns are a right."')
    text, metadata = debater.generate_turn([])

    assert text == "Guns are a right."
    assert metadata["raw_text"] == '"Guns are a right."'
    assert len(metadata["system_prompt_sha256"]) == 64


def test_generate_turn_sends_composed_prompt_and_history():
    debater = make_debater("Reply.")
    client = debater.client
    debater.generate_turn(
        [PublishedMessage(turn=1, persona_id="persona_2", text="Opening.")]
    )

    system_prompt, user_message = client.calls[0]
    assert "HOW YOU DEBATE" in system_prompt
    assert "Gun Ownership" in system_prompt
    assert "OPPONENT]: Opening." in user_message


def test_debater_requires_persona_source():
    with pytest.raises(ValueError, match="persona_prompt"):
        Debater(
            client=FakeClient(),
            persona_id="persona_1",
            topic="Gun Ownership",
        )


def test_empty_reply_raises_rather_than_publishing_blank():
    debater = make_debater("   ")

    with pytest.raises(DebaterError):
        debater.generate_turn([])
