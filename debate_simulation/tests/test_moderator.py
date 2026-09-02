"""Tests for the D5 moderator orchestration and JSON parsing.

No network: the LLM is a fake returning scripted replies, so these cover the
parsing cascade, the retry, the consistency check and record construction
without spending API calls.
"""

from __future__ import annotations

import json

import pytest

from moderator.moderator import (
    REPARSE_INSTRUCTION,
    STRATEGY_BLOCK,
    STRATEGY_DIRECT,
    STRATEGY_FENCE,
    STRATEGY_QUOTES,
    STRATEGY_RETRY,
    D5Moderator,
    ModerationParseError,
    parse_moderation_response,
    parse_moderation_response_with_strategy,
)
from moderator.schema import ModerationRequest, ModerationResponse, PublishedMessage

SYSTEM_PROMPT = "test system prompt"

HOSTILE_VERDICT = {
    "hostility_level": 3,
    "pathologies_detected": ["rhetoric_of_incomprehension"],
    "justification": "Calls the opponent a moron; attacks the person.",
    "requires_intervention": True,
    "reformulation": "That argument ignores the actual data.",
    "argument_preserved": "The claim that the data is being ignored.",
}

CLEAN_VERDICT = {
    "hostility_level": 0,
    "pathologies_detected": [],
    "justification": "Disagreement is directed at the policy, not the person.",
    "requires_intervention": False,
    "reformulation": None,
    "argument_preserved": None,
}


class FakeClient:
    """Stands in for LLMClient, returning scripted replies in order."""

    def __init__(self, *replies: str) -> None:
        self.replies = list(replies)
        self.calls: list[tuple[str, str]] = []

    def call(self, system_prompt: str, user_message: str) -> tuple[str, dict]:
        self.calls.append((system_prompt, user_message))
        if not self.replies:
            raise AssertionError("FakeClient ran out of scripted replies")
        return self.replies.pop(0), {
            "model": "fake-model",
            "provider": "fake",
            "temperature": 0.2,
            "latency_ms": 100,
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "attempts": 1,
        }


class RecordingLogger:
    """Captures records instead of writing them, matching ModerationLogger."""

    def __init__(self) -> None:
        self.records: list = []
        self.failures: list[dict] = []

    def log_moderation(self, record) -> None:
        self.records.append(record)

    def log_failure(self, **kwargs) -> None:
        self.failures.append(kwargs)


def make_request(candidate: str = "You are a moron.") -> ModerationRequest:
    return ModerationRequest(
        topic="Gun Ownership",
        persona_id="persona_2",
        history=[PublishedMessage(turn=1, persona_id="persona_1", text="Opening.")],
        candidate=candidate,
    )


def make_moderator(*replies: str, logger=None) -> tuple[D5Moderator, FakeClient]:
    client = FakeClient(*replies)
    moderator = D5Moderator(
        client=client, logger=logger, system_prompt=SYSTEM_PROMPT
    )
    return moderator, client


# --- parsing cascade -------------------------------------------------------


def test_parses_bare_json():
    response = parse_moderation_response(json.dumps(HOSTILE_VERDICT))
    assert response.hostility_level == 3
    assert response.requires_intervention is True


def test_parses_json_wrapped_in_markdown_fence():
    fenced = f"```json\n{json.dumps(HOSTILE_VERDICT)}\n```"
    assert parse_moderation_response(fenced).hostility_level == 3


def test_parses_json_wrapped_in_bare_fence():
    fenced = f"```\n{json.dumps(CLEAN_VERDICT)}\n```"
    assert parse_moderation_response(fenced).requires_intervention is False


def test_extracts_json_after_reasoning_preamble():
    """The Nemotron case: reasoning text before the object."""
    text = (
        "Let me think about this. The message attacks the person directly.\n\n"
        f"{json.dumps(HOSTILE_VERDICT)}\n\nThat is my assessment."
    )
    assert parse_moderation_response(text).hostility_level == 3


def test_extraction_handles_braces_inside_strings():
    verdict = dict(HOSTILE_VERDICT, justification='They wrote "}" to derail.')
    text = f"Preamble.\n{json.dumps(verdict)}"
    assert parse_moderation_response(text).justification == 'They wrote "}" to derail.'


def test_repairs_unescaped_quotes_from_cited_text():
    """The moderator is told to quote the candidate; the quotes break JSON.

    Observed in a real run: justification citing 'precious "gun control"
    measures' produced invalid JSON and lost the whole turn.
    """
    raw = (
        '{"hostility_level": 3, '
        '"pathologies_detected": ["rhetoric_of_incomprehension"], '
        '"justification": "Uses contempt (\'precious "gun control" measures\').", '
        '"requires_intervention": true, '
        '"reformulation": "That policy claim does not hold up.", '
        '"argument_preserved": "The objection to the policy."}'
    )
    response, strategy = parse_moderation_response_with_strategy(raw)

    assert strategy == STRATEGY_QUOTES
    assert response.hostility_level == 3
    assert '"gun control"' in response.justification


def test_repair_is_not_applied_to_valid_json():
    """A reply that parses as-is must never be rewritten."""
    _, strategy = parse_moderation_response_with_strategy(json.dumps(HOSTILE_VERDICT))
    assert strategy == STRATEGY_DIRECT


def test_raises_on_unparseable_text_carrying_raw_response():
    with pytest.raises(ModerationParseError) as exc_info:
        parse_moderation_response("I cannot comply with this request.")
    assert exc_info.value.raw_response == "I cannot comply with this request."


def test_raises_on_valid_json_violating_contract():
    """Hostility outside 0-4 is a contract violation, not malformed JSON."""
    bad = dict(HOSTILE_VERDICT, hostility_level=9)
    with pytest.raises(ModerationParseError):
        parse_moderation_response(json.dumps(bad))


def test_raises_when_intervention_lacks_reformulation():
    bad = dict(HOSTILE_VERDICT, reformulation=None)
    with pytest.raises(ModerationParseError):
        parse_moderation_response(json.dumps(bad))


def test_raises_when_reformulation_present_without_intervention():
    """A reformulation nobody asked for would silently replace the candidate."""
    bad = dict(CLEAN_VERDICT, reformulation="Rewritten anyway.")
    with pytest.raises(ModerationParseError):
        parse_moderation_response(json.dumps(bad))


def test_raises_on_unknown_pathology():
    bad = dict(HOSTILE_VERDICT, pathologies_detected=["ad_hominem"])
    with pytest.raises(ModerationParseError):
        parse_moderation_response(json.dumps(bad))


@pytest.mark.parametrize("level", [-1, 5, 10])
def test_raises_on_hostility_outside_scale(level):
    bad = dict(HOSTILE_VERDICT, hostility_level=level)
    with pytest.raises(ModerationParseError):
        parse_moderation_response(json.dumps(bad))


# --- moderate() ------------------------------------------------------------


def test_moderate_returns_validated_response():
    moderator, client = make_moderator(json.dumps(HOSTILE_VERDICT))
    response = moderator.moderate(make_request())

    assert isinstance(response, ModerationResponse)
    assert response.hostility_level == 3
    assert len(client.calls) == 1


def test_moderate_sends_system_prompt_and_rendered_request():
    moderator, client = make_moderator(json.dumps(CLEAN_VERDICT))
    moderator.moderate(make_request(candidate="A civil point."))

    system_prompt, user_message = client.calls[0]
    assert system_prompt == SYSTEM_PROMPT
    assert "TOPIC: Gun Ownership" in user_message
    assert "A civil point." in user_message


def test_moderate_retries_once_on_unparseable_reply():
    moderator, client = make_moderator(
        "I'm not sure how to answer that.", json.dumps(HOSTILE_VERDICT)
    )
    response = moderator.moderate(make_request())

    assert response.hostility_level == 3
    assert len(client.calls) == 2
    assert client.calls[1][1].endswith(REPARSE_INSTRUCTION)


def test_retry_is_recorded_as_parse_recovery():
    logger = RecordingLogger()
    moderator, _ = make_moderator(
        "garbage", json.dumps(HOSTILE_VERDICT), logger=logger
    )
    moderator.moderate(make_request())

    assert logger.records[0].model_call["parse_recovery_used"] is True


def test_no_recovery_flag_when_first_reply_parses():
    logger = RecordingLogger()
    moderator, _ = make_moderator(json.dumps(HOSTILE_VERDICT), logger=logger)
    moderator.moderate(make_request())

    model_call = logger.records[0].model_call
    assert model_call["parse_recovery_used"] is False
    assert model_call["parse_strategy"] == STRATEGY_DIRECT


@pytest.mark.parametrize(
    ("reply", "expected_strategy"),
    [
        (json.dumps(HOSTILE_VERDICT), STRATEGY_DIRECT),
        (f"```json\n{json.dumps(HOSTILE_VERDICT)}\n```", STRATEGY_FENCE),
        (f"Let me think.\n{json.dumps(HOSTILE_VERDICT)}", STRATEGY_BLOCK),
    ],
)
def test_parse_strategy_is_recorded(reply, expected_strategy):
    """How often a model needs recovery is a finding about that model."""
    logger = RecordingLogger()
    moderator, client = make_moderator(reply, logger=logger)
    moderator.moderate(make_request())

    model_call = logger.records[0].model_call
    assert model_call["parse_strategy"] == expected_strategy
    assert model_call["parse_recovery_used"] is (expected_strategy != STRATEGY_DIRECT)
    assert len(client.calls) == 1  # recovered without a second call


def test_recovery_flag_set_without_a_retry_call():
    """Item 8: fence stripping alone counts as recovery."""
    logger = RecordingLogger()
    fenced = f"```json\n{json.dumps(CLEAN_VERDICT)}\n```"
    moderator, client = make_moderator(fenced, logger=logger)
    moderator.moderate(make_request())

    assert logger.records[0].model_call["parse_recovery_used"] is True
    assert len(client.calls) == 1


def test_moderate_raises_when_retry_also_fails():
    moderator, client = make_moderator("garbage", "still garbage")

    with pytest.raises(ModerationParseError) as exc_info:
        moderator.moderate(make_request())

    assert exc_info.value.raw_response == "still garbage"
    assert len(client.calls) == 2


def test_failure_is_logged_before_raising():
    logger = RecordingLogger()
    moderator, _ = make_moderator("garbage", "still garbage", logger=logger)

    with pytest.raises(ModerationParseError):
        moderator.moderate(make_request())

    assert len(logger.failures) == 1
    failure = logger.failures[0]
    assert failure["raw_response"] == "still garbage"
    assert failure["persona_id"] == "persona_2"
    assert failure["model_call"]["calls"] == 2  # both calls, not just the first
    assert logger.records == []  # never a fabricated success record


def test_retry_metadata_sums_both_calls():
    logger = RecordingLogger()
    moderator, _ = make_moderator(
        "garbage", json.dumps(HOSTILE_VERDICT), logger=logger
    )
    moderator.moderate(make_request())

    model_call = logger.records[0].model_call
    assert model_call["calls"] == 2
    assert model_call["latency_ms"] == 200  # 100 per fake call
    assert model_call["attempts"] == 2


# --- resolve_published_text ------------------------------------------------


def test_publishes_reformulation_when_intervened():
    moderator, _ = make_moderator()
    request = make_request()
    response = ModerationResponse.model_validate(HOSTILE_VERDICT)

    published = moderator.resolve_published_text(request, response)
    assert published == HOSTILE_VERDICT["reformulation"]


def test_publishes_candidate_when_not_intervened():
    moderator, _ = make_moderator()
    request = make_request(candidate="A civil point.")
    response = ModerationResponse.model_validate(CLEAN_VERDICT)

    assert moderator.resolve_published_text(request, response) == "A civil point."


# --- consistency check -----------------------------------------------------


def test_no_warning_when_score_and_decision_agree():
    logger = RecordingLogger()
    moderator, _ = make_moderator(json.dumps(HOSTILE_VERDICT), logger=logger)
    moderator.moderate(make_request())

    assert logger.records[0].consistency_warning is None


def test_warns_when_above_threshold_without_intervening():
    """Level 3 with no intervention: recorded, never overridden."""
    inconsistent = dict(
        CLEAN_VERDICT,
        hostility_level=3,
        requires_intervention=False,
    )
    logger = RecordingLogger()
    moderator, _ = make_moderator(json.dumps(inconsistent), logger=logger)
    response = moderator.moderate(make_request())

    assert response.requires_intervention is False  # model's decision stands
    warning = logger.records[0].consistency_warning
    assert warning is not None
    assert "Did not intervene" in warning


def test_warns_when_intervening_below_threshold():
    inconsistent = dict(HOSTILE_VERDICT, hostility_level=1)
    logger = RecordingLogger()
    moderator, _ = make_moderator(json.dumps(inconsistent), logger=logger)
    response = moderator.moderate(make_request())

    assert response.requires_intervention is True
    assert "Intervened" in logger.records[0].consistency_warning


def test_inconsistent_verdict_still_publishes_per_model_decision():
    """A warning must not change what gets published."""
    inconsistent = dict(
        CLEAN_VERDICT, hostility_level=4, requires_intervention=False
    )
    moderator, _ = make_moderator(json.dumps(inconsistent))
    request = make_request(candidate="Hostile text.")
    response = moderator.moderate(request)

    assert moderator.resolve_published_text(request, response) == "Hostile text."


# --- record construction ---------------------------------------------------


def test_record_carries_resolution_and_identity():
    logger = RecordingLogger()
    moderator, _ = make_moderator(json.dumps(HOSTILE_VERDICT), logger=logger)
    moderator.moderate(make_request(), experiment_id="exp-1", turn=2)

    record = logger.records[0]
    assert record.experiment_id == "exp-1"
    assert record.turn == 2
    assert record.persona_id == "persona_2"
    assert record.topic == "Gun Ownership"
    assert record.resolution["was_reformulated"] is True
    assert record.resolution["published_source"] == "reformulation"
    assert record.resolution["published_text"] == HOSTILE_VERDICT["reformulation"]


def test_turn_defaults_to_position_after_history():
    logger = RecordingLogger()
    moderator, _ = make_moderator(json.dumps(CLEAN_VERDICT), logger=logger)
    moderator.moderate(make_request())  # history has 1 message

    assert logger.records[0].turn == 2


def test_injected_prompt_records_no_digest():
    """Hashing the file would misidentify a prompt that did not come from it."""
    logger = RecordingLogger()
    moderator, _ = make_moderator(json.dumps(CLEAN_VERDICT), logger=logger)
    moderator.moderate(make_request())

    assert logger.records[0].model_call["system_prompt_sha256"] is None


def test_moderate_works_without_a_logger():
    moderator, _ = make_moderator(json.dumps(HOSTILE_VERDICT))
    assert moderator.moderate(make_request()).hostility_level == 3
