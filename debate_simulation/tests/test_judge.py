"""Tests for the hostility judge. No network."""

from __future__ import annotations

import json
import re

import pytest

from judge.judge import (
    HostilityJudge,
    JudgementParseError,
    judge_transcript,
    parse_judgement_response,
)
from judge.logger import JudgementLogger
from judge.prompt import (
    EMPTY_CONTEXT_TEXT,
    build_user_message,
    load_system_prompt,
    prompt_sha256,
)
from judge.schema import RUNS_PER_MESSAGE, JudgementRequest
from moderator.schema import PublishedMessage

from tests.test_moderator import FakeClient

SCORE_3 = {
    "hostility_level": 3,
    "pathologies_detected": ["rhetoric_of_incomprehension"],
    "justification": "Calls the opponent brainwashed; attacks the person.",
    "targets_person": True,
}

SCORE_0 = {
    "hostility_level": 0,
    "pathologies_detected": [],
    "justification": "Disagreement is aimed at the policy, not the person.",
    "targets_person": False,
}


def make_request(message: str = "You are brainwashed.", turn: int = 2):
    return JudgementRequest(
        topic="Gun Ownership",
        persona_id="persona_2",
        turn=turn,
        message=message,
        context=[PublishedMessage(turn=1, persona_id="persona_1", text="Opening.")],
    )


def make_judge(*replies: str, logger=None, runs: int = RUNS_PER_MESSAGE):
    client = FakeClient(*replies)
    judge = HostilityJudge(
        client=client,
        logger=logger,
        system_prompt="judge prompt",
        runs_per_message=runs,
    )
    return judge, client


def scored(*verdicts) -> list[str]:
    return [json.dumps(v) for v in verdicts]


class RecordingLogger:
    def __init__(self):
        self.records = []

    def log_judgement(self, record):
        self.records.append(record)


# --- prompt ----------------------------------------------------------------


def test_user_message_layout():
    message = build_user_message(make_request())

    assert message.startswith("TOPIC: Gun Ownership")
    for section in ("CONTEXT:", "PERSONA: Persona 2", "MESSAGE:"):
        assert section in message
    assert message.rstrip().endswith("You are brainwashed.")


def test_context_excludes_the_message_being_scored():
    """Including it twice would let the context inflate its own score."""
    request = JudgementRequest(
        topic="Gun Ownership",
        persona_id="persona_1",
        turn=2,
        message="Scored message.",
        context=[
            PublishedMessage(turn=1, persona_id="persona_1", text="Earlier."),
            PublishedMessage(turn=2, persona_id="persona_1", text="Scored message."),
            PublishedMessage(turn=3, persona_id="persona_2", text="Later."),
        ],
    )
    message = build_user_message(request)

    assert "Earlier." in message
    assert "Later." not in message
    assert message.count("Scored message.") == 1


def test_opening_message_has_empty_context():
    request = JudgementRequest(
        topic="Abortion", persona_id="persona_1", turn=1, message="Opening."
    )
    assert EMPTY_CONTEXT_TEXT in build_user_message(request)


def test_context_is_ordered_by_turn():
    request = JudgementRequest(
        topic="Gun Ownership",
        persona_id="persona_1",
        turn=3,
        message="Third.",
        context=[
            PublishedMessage(turn=2, persona_id="persona_2", text="Second."),
            PublishedMessage(turn=1, persona_id="persona_1", text="First."),
        ],
    )
    message = build_user_message(request)

    assert message.index("First.") < message.index("Second.")


def test_judge_prompt_carries_no_pole_label():
    lowered = build_user_message(make_request()).lower()

    for term in ("left", "right", "pole", "esquerda", "direita", "treatment", "control"):
        assert not re.search(rf"\b{term}\b", lowered)


def test_system_prompt_loads_and_hashes():
    prompt = load_system_prompt()

    assert "Hostility Judge" in prompt
    assert "HOSTILITY SCALE" in prompt
    assert len(prompt_sha256()) == 64


def test_system_prompt_forbids_scoring_content():
    lowered = load_system_prompt().lower()

    assert "ideologically neutral" in lowered
    assert "not evaluating whether" in lowered


def test_unknown_persona_raises():
    request = JudgementRequest(
        topic="Abortion", persona_id="persona_9", turn=1, message="Hi."
    )
    with pytest.raises(ValueError, match="Unknown persona_id"):
        build_user_message(request)


# --- parsing ---------------------------------------------------------------


def test_parses_bare_json():
    response, strategy = parse_judgement_response(json.dumps(SCORE_3))

    assert response.hostility_level == 3
    assert response.targets_person is True
    assert strategy == "direct"


def test_parses_json_after_preamble():
    response, strategy = parse_judgement_response(f"Thinking...\n{json.dumps(SCORE_0)}")

    assert response.hostility_level == 0
    assert strategy == "block_extracted"


def test_rejects_score_outside_scale():
    with pytest.raises(JudgementParseError):
        parse_judgement_response(json.dumps(dict(SCORE_3, hostility_level=7)))


def test_rejects_unknown_pathology():
    bad = dict(SCORE_3, pathologies_detected=["ad_hominem"])
    with pytest.raises(JudgementParseError):
        parse_judgement_response(json.dumps(bad))


def test_pathologies_default_to_empty():
    minimal = {
        "hostility_level": 0,
        "justification": "Nothing hostile.",
        "targets_person": False,
    }
    assert parse_judgement_response(json.dumps(minimal))[0].pathologies_detected == []


# --- repeated runs ---------------------------------------------------------


def test_scores_each_message_three_times_by_default():
    judge, client = make_judge(*scored(SCORE_3, SCORE_3, SCORE_3))
    record = judge.judge_message(make_request())

    assert len(record.runs) == RUNS_PER_MESSAGE == 3
    assert len(client.calls) == 3
    assert [r.run_index for r in record.runs] == [1, 2, 3]


def test_identical_inputs_across_runs():
    """Runs must differ only by the model's own variation."""
    judge, client = make_judge(*scored(SCORE_3, SCORE_3, SCORE_3))
    judge.judge_message(make_request())

    assert len({user for _, user in client.calls}) == 1


def test_unanimous_runs_summarize_cleanly():
    judge, _ = make_judge(*scored(SCORE_3, SCORE_3, SCORE_3))
    record = judge.judge_message(make_request())

    assert record.scores == [3, 3, 3]
    assert record.median_score == 3
    assert record.score_range == 0
    assert record.unanimous is True


def test_disagreement_is_preserved_not_averaged_away():
    """Every run is kept; the summary is derived from them."""
    judge, _ = make_judge(
        *scored(SCORE_3, dict(SCORE_3, hostility_level=2), dict(SCORE_3, hostility_level=4))
    )
    record = judge.judge_message(make_request())

    assert record.scores == [3, 2, 4]
    assert record.median_score == 3
    assert record.score_range == 2
    assert record.unanimous is False
    assert record.summary()["runs"] == 3


def test_runs_can_be_configured():
    judge, client = make_judge(*scored(SCORE_0), runs=1)
    record = judge.judge_message(make_request())

    assert len(record.runs) == 1
    assert len(client.calls) == 1


def test_zero_runs_rejected():
    with pytest.raises(ValueError, match="at least 1"):
        HostilityJudge(client=FakeClient(), system_prompt="p", runs_per_message=0)


def test_retry_on_unparseable_run():
    judge, client = make_judge(
        "garbage", json.dumps(SCORE_3), json.dumps(SCORE_3), json.dumps(SCORE_3), runs=3
    )
    record = judge.judge_message(make_request())

    assert len(record.runs) == 3
    assert len(client.calls) == 4  # one extra for the retry
    assert record.runs[0].model_call["parse_recovery_used"] is True


def test_irrecoverable_failure_raises_rather_than_scoring_zero():
    judge, _ = make_judge("garbage", "still garbage", runs=1)

    with pytest.raises(JudgementParseError):
        judge.judge_message(make_request())


def test_record_carries_identity_and_condition():
    judge, _ = make_judge(*scored(SCORE_3, SCORE_3, SCORE_3))
    record = judge.judge_message(
        make_request(), experiment_id="exp-1", condition="treatment"
    )

    assert record.experiment_id == "exp-1"
    assert record.condition == "treatment"
    assert record.turn == 2
    assert record.persona_id == "persona_2"
    assert record.context_length == 1


# --- judging a whole transcript -------------------------------------------


def test_judge_transcript_scores_every_message():
    transcript = [
        PublishedMessage(turn=1, persona_id="persona_1", text="A."),
        PublishedMessage(turn=2, persona_id="persona_2", text="B."),
    ]
    judge, _ = make_judge(*scored(*([SCORE_0] * 6)))
    records = judge_transcript(judge, "Gun Ownership", "control", transcript)

    assert [r.turn for r in records] == [1, 2]
    assert all(len(r.runs) == 3 for r in records)


def test_each_message_sees_only_prior_context():
    transcript = [
        PublishedMessage(turn=1, persona_id="persona_1", text="First."),
        PublishedMessage(turn=2, persona_id="persona_2", text="Second."),
    ]
    judge, client = make_judge(*scored(*([SCORE_0] * 6)), runs=1)
    judge.runs_per_message = 1
    judge_transcript(judge, "Gun Ownership", "control", transcript)

    first_call = client.calls[0][1]
    second_call = client.calls[1][1]
    assert EMPTY_CONTEXT_TEXT in first_call
    assert "First." in second_call


def test_transcript_order_is_normalized():
    transcript = [
        PublishedMessage(turn=2, persona_id="persona_2", text="Second."),
        PublishedMessage(turn=1, persona_id="persona_1", text="First."),
    ]
    judge, _ = make_judge(*scored(*([SCORE_0] * 6)))
    records = judge_transcript(judge, "Gun Ownership", "control", transcript)

    assert [r.turn for r in records] == [1, 2]


# --- logging ---------------------------------------------------------------


def test_logged_record_keeps_every_run(tmp_path):
    logger = JudgementLogger("exp-1", base_dir=tmp_path)
    judge, _ = make_judge(
        *scored(SCORE_3, dict(SCORE_3, hostility_level=2), SCORE_3), logger=logger
    )
    judge.judge_message(make_request(), experiment_id="exp-1", condition="treatment")

    path = tmp_path / "exp-1" / "judgements" / "turn_002_persona_2.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert len(payload["runs"]) == 3
    assert [r["hostility_level"] for r in payload["runs"]] == [3, 2, 3]
    assert payload["summary"]["median"] == 3
    assert payload["summary"]["unanimous"] is False
    assert payload["condition"] == "treatment"


def test_judgements_never_overwrite(tmp_path):
    logger = JudgementLogger("exp-1", base_dir=tmp_path)
    judge, _ = make_judge(*scored(*([SCORE_0] * 6)), logger=logger)
    judge.judge_message(make_request())
    judge.judge_message(make_request())

    files = sorted(p.name for p in (tmp_path / "exp-1" / "judgements").glob("*.json"))
    assert files == ["turn_002_persona_2.json", "turn_002_persona_2_2.json"]


def test_judged_messages_supports_resumption(tmp_path):
    logger = JudgementLogger("exp-1", base_dir=tmp_path)
    judge, _ = make_judge(*scored(*([SCORE_0] * 6)), logger=logger)
    judge.judge_message(make_request(turn=1))
    judge.judge_message(make_request(turn=2))

    assert logger.judged_messages() == {(1, "persona_2"), (2, "persona_2")}


def test_load_scores_returns_summaries_in_order(tmp_path):
    logger = JudgementLogger("exp-1", base_dir=tmp_path)
    judge, _ = make_judge(*scored(*([SCORE_3] * 6)), logger=logger)
    judge.judge_message(make_request(turn=2), condition="control")
    judge.judge_message(make_request(turn=1), condition="control")

    scores = logger.load_scores()
    assert [s["turn"] for s in scores] == [1, 2]
    assert all(s["median"] == 3 for s in scores)


def test_failure_record_is_written(tmp_path):
    logger = JudgementLogger("exp-1", base_dir=tmp_path)
    path = logger.log_failure(
        turn=3,
        persona_id="persona_1",
        error=JudgementParseError("bad", raw_response="I refuse."),
        raw_response="I refuse.",
        run_index=2,
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == "turn_003_persona_1_FAILED.json"
    assert payload["status"] == "FAILED"
    assert payload["raw_response"] == "I refuse."
    assert payload["run_index"] == 2
    assert logger.judged_messages() == set()  # a failure is not a judgement