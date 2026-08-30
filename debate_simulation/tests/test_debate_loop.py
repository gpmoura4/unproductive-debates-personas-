"""Tests for the debate loop, in both conditions. No network."""

from __future__ import annotations

import json

import pytest

from debate.loop import (
    CONTROL,
    TREATMENT,
    DebateLoop,
    speaker_for_turn,
    write_transcript,
)
from debater.debater import Debater
from moderator.moderator import D5Moderator
from moderator.schema import PublishedMessage

from tests.test_moderator import CLEAN_VERDICT, HOSTILE_VERDICT, FakeClient

TOPIC = "Gun Ownership"


def make_debaters(*, replies_1: list[str], replies_2: list[str]) -> dict[str, Debater]:
    return {
        "persona_1": Debater(
            client=FakeClient(*replies_1),
            persona_id="persona_1",
            topic=TOPIC,
            persona_prompt="Persona one.",
            behavior_prompt="Be hostile.",
        ),
        "persona_2": Debater(
            client=FakeClient(*replies_2),
            persona_id="persona_2",
            topic=TOPIC,
            persona_prompt="Persona two.",
            behavior_prompt="Be hostile.",
        ),
    }


def make_moderator(*replies: str, logger=None) -> D5Moderator:
    return D5Moderator(
        client=FakeClient(*replies), logger=logger, system_prompt="moderator prompt"
    )


def make_loop(condition=CONTROL, debaters=None, moderator=None) -> DebateLoop:
    return DebateLoop(
        experiment_id="exp-1",
        topic=TOPIC,
        condition=condition,
        debaters=debaters
        or make_debaters(replies_1=["A1", "A2"], replies_2=["B1", "B2"]),
        moderator=moderator,
    )


# --- turn order ------------------------------------------------------------


def test_persona_1_opens_and_they_alternate():
    assert [speaker_for_turn(t) for t in range(1, 6)] == [
        "persona_1",
        "persona_2",
        "persona_1",
        "persona_2",
        "persona_1",
    ]


# --- control condition -----------------------------------------------------


def test_control_publishes_candidates_unchanged():
    result = make_loop(CONTROL).run(planned_turns=4)

    assert result.completed is True
    assert [t.published_text for t in result.turns] == ["A1", "B1", "A2", "B2"]
    assert all(t.candidate == t.published_text for t in result.turns)
    assert result.intervention_count == 0


def test_control_marks_turns_unmoderated():
    """No moderator ran, so no turn carries a verdict."""
    result = make_loop(CONTROL).run(planned_turns=2)

    assert all(t.moderated is False for t in result.turns)
    assert all(t.hostility_level is None for t in result.turns)


def test_control_rejects_a_moderator_it_would_ignore():
    """A moderator passed to control would silently do nothing."""
    loop = DebateLoop(
        experiment_id="exp-1",
        topic=TOPIC,
        condition=CONTROL,
        debaters=make_debaters(replies_1=["A1"], replies_2=["B1"]),
        moderator=make_moderator(),
    )
    result = loop.run(planned_turns=2)

    assert result.intervention_count == 0


def test_treatment_without_moderator_raises():
    with pytest.raises(ValueError, match="requires a moderator"):
        DebateLoop(
            experiment_id="exp-1",
            topic=TOPIC,
            condition=TREATMENT,
            debaters=make_debaters(replies_1=["A1"], replies_2=["B1"]),
        )


def test_unknown_condition_raises():
    with pytest.raises(ValueError, match="Unknown condition"):
        DebateLoop(
            experiment_id="exp-1",
            topic=TOPIC,
            condition="placebo",
            debaters=make_debaters(replies_1=["A1"], replies_2=["B1"]),
        )


def test_missing_debater_raises():
    with pytest.raises(ValueError, match="Missing debaters"):
        DebateLoop(
            experiment_id="exp-1",
            topic=TOPIC,
            condition=CONTROL,
            debaters={"persona_1": make_debaters(replies_1=["A"], replies_2=["B"])["persona_1"]},
        )


# --- treatment condition ---------------------------------------------------


def test_treatment_publishes_the_reformulation():
    loop = make_loop(
        TREATMENT,
        debaters=make_debaters(replies_1=["hostile A"], replies_2=["hostile B"]),
        moderator=make_moderator(json.dumps(HOSTILE_VERDICT), json.dumps(HOSTILE_VERDICT)),
    )
    result = loop.run(planned_turns=2)

    assert all(t.was_reformulated for t in result.turns)
    assert result.turns[0].candidate == "hostile A"
    assert result.turns[0].published_text == HOSTILE_VERDICT["reformulation"]
    assert result.intervention_count == 2


def test_treatment_publishes_candidate_when_clean():
    loop = make_loop(
        TREATMENT,
        debaters=make_debaters(replies_1=["civil A"], replies_2=["civil B"]),
        moderator=make_moderator(json.dumps(CLEAN_VERDICT), json.dumps(CLEAN_VERDICT)),
    )
    result = loop.run(planned_turns=2)

    assert [t.published_text for t in result.turns] == ["civil A", "civil B"]
    assert result.intervention_count == 0


def test_opponent_replies_to_the_published_text():
    """This is what propagates the D5 effect through the debate."""
    debaters = make_debaters(replies_1=["hostile A"], replies_2=["B reply"])
    loop = make_loop(
        TREATMENT,
        debaters=debaters,
        moderator=make_moderator(json.dumps(HOSTILE_VERDICT), json.dumps(CLEAN_VERDICT)),
    )
    loop.run(planned_turns=2)

    _, user_message = debaters["persona_2"].client.calls[0]
    assert HOSTILE_VERDICT["reformulation"] in user_message
    assert "hostile A" not in user_message


def test_treatment_records_verdict_details():
    loop = make_loop(
        TREATMENT,
        debaters=make_debaters(replies_1=["hostile A"], replies_2=["B"]),
        moderator=make_moderator(json.dumps(HOSTILE_VERDICT)),
    )
    turn = loop.run(planned_turns=1).turns[0]

    assert turn.moderated is True
    assert turn.hostility_level == 3
    assert turn.pathologies_detected == ["rhetoric_of_incomprehension"]


def test_consistency_warning_reaches_the_turn():
    inconsistent = dict(CLEAN_VERDICT, hostility_level=3, requires_intervention=False)
    loop = make_loop(
        TREATMENT,
        debaters=make_debaters(replies_1=["A"], replies_2=["B"]),
        moderator=make_moderator(json.dumps(inconsistent)),
    )
    turn = loop.run(planned_turns=1).turns[0]

    assert turn.consistency_warning is not None
    assert "Did not intervene" in turn.consistency_warning


# --- moderation failure ----------------------------------------------------


def test_moderation_failure_publishes_candidate_and_continues():
    """A failed verdict must not cost the rest of the debate."""
    loop = make_loop(
        TREATMENT,
        debaters=make_debaters(replies_1=["A1"], replies_2=["B1"]),
        # Turn 1: two unusable replies. Turn 2: a valid verdict.
        moderator=make_moderator("garbage", "still garbage", json.dumps(CLEAN_VERDICT)),
    )
    result = loop.run(planned_turns=2)

    assert result.completed is True
    failed_turn = result.turns[0]
    assert failed_turn.moderated is False
    assert failed_turn.published_text == "A1"  # the candidate, unmoderated
    assert failed_turn.moderation_error is not None
    assert result.turns[1].moderated is True


def test_unmoderated_turns_are_reported():
    """Averaging hostility over these would understate the intervention."""
    loop = make_loop(
        TREATMENT,
        debaters=make_debaters(replies_1=["A1"], replies_2=["B1"]),
        moderator=make_moderator("garbage", "still garbage", json.dumps(CLEAN_VERDICT)),
    )
    result = loop.run(planned_turns=2)

    assert result.unmoderated_turns == [1]


def test_debater_failure_stops_and_keeps_partial_turns():
    loop = make_loop(
        CONTROL, debaters=make_debaters(replies_1=["A1"], replies_2=["   "])
    )
    result = loop.run(planned_turns=4)

    assert result.completed is False
    assert len(result.turns) == 1  # turn 1 survived
    assert "DebaterError" in result.stopped_reason


# --- resumption ------------------------------------------------------------


def test_run_resumes_from_existing_history():
    history = [
        PublishedMessage(turn=1, persona_id="persona_1", text="Earlier A."),
        PublishedMessage(turn=2, persona_id="persona_2", text="Earlier B."),
    ]
    loop = make_loop(
        CONTROL, debaters=make_debaters(replies_1=["A2"], replies_2=["B2"])
    )
    result = loop.run(planned_turns=4, history=history)

    # Only the two remaining turns were generated.
    assert [t.turn for t in result.turns] == [3, 4]
    assert [t.published_text for t in result.turns] == ["A2", "B2"]


def test_resumed_turn_sees_prior_history():
    history = [PublishedMessage(turn=1, persona_id="persona_1", text="Earlier A.")]
    debaters = make_debaters(replies_1=[], replies_2=["B1"])
    loop = make_loop(CONTROL, debaters=debaters)
    loop.run(planned_turns=2, history=history)

    _, user_message = debaters["persona_2"].client.calls[0]
    assert "Earlier A." in user_message


def test_on_turn_callback_fires_per_turn():
    seen = []
    make_loop(CONTROL).run(planned_turns=3, on_turn=seen.append)

    assert [t.turn for t in seen] == [1, 2, 3]


# --- transcript ------------------------------------------------------------


def test_transcript_records_both_texts_and_flags(tmp_path):
    loop = make_loop(
        TREATMENT,
        debaters=make_debaters(replies_1=["hostile A"], replies_2=["B"]),
        moderator=make_moderator(json.dumps(HOSTILE_VERDICT), json.dumps(CLEAN_VERDICT)),
    )
    result = loop.run(planned_turns=2)
    path = write_transcript(result, tmp_path)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == "transcript.json"
    assert payload["condition"] == TREATMENT
    assert payload["turn_count"] == 2
    assert payload["intervention_count"] == 1
    assert payload["unmoderated_turns"] == []

    first = payload["turns"][0]
    assert first["candidate"] == "hostile A"
    assert first["published_text"] == HOSTILE_VERDICT["reformulation"]
    assert first["was_reformulated"] is True


def test_transcript_written_for_control_too(tmp_path):
    """Control produces no moderation records, so it needs its own transcript."""
    result = make_loop(CONTROL).run(planned_turns=2)
    payload = json.loads(write_transcript(result, tmp_path).read_text(encoding="utf-8"))

    assert payload["condition"] == CONTROL
    assert payload["turn_count"] == 2
    assert payload["intervention_count"] == 0


def test_incomplete_debate_still_writes_a_transcript(tmp_path):
    loop = make_loop(CONTROL, debaters=make_debaters(replies_1=["A1"], replies_2=[""]))
    result = loop.run(planned_turns=4)
    payload = json.loads(write_transcript(result, tmp_path).read_text(encoding="utf-8"))

    assert payload["completed"] is False
    assert payload["stopped_reason"] is not None
    assert payload["turn_count"] == 1
