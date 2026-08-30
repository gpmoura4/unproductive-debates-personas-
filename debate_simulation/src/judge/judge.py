"""Hostility judging (Model C).

Scores each published message `RUNS_PER_MESSAGE` times so intra-judge
consistency is measurable. The runs are independent calls with identical
inputs — at temperature 0 they should agree, and where they do not, the
disagreement is data about the judge rather than noise to average away.

Failure policy matches the moderator's: a run that cannot be parsed after one
corrective call raises, and no placeholder score is ever returned. A fabricated
"0" would enter the analysis as if the judge had scored the message.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from llm.client import LLMClient
from llm.parsing import (
    STRATEGY_DIRECT,
    STRATEGY_RETRY,
    ResponseParseError,
    merge_call_metadata,
    parse_json_response,
)

from judge.prompt import build_user_message, load_system_prompt, prompt_sha256
from judge.schema import (
    RUNS_PER_MESSAGE,
    JudgementRecord,
    JudgementRequest,
    JudgementResponse,
    JudgementRun,
)

if TYPE_CHECKING:
    from judge.logger import JudgementLogger

REPARSE_INSTRUCTION = (
    "\n\nYour previous response was not valid JSON. Respond with ONLY the "
    "JSON object."
)


class JudgementParseError(ResponseParseError):
    """A judge reply could not be parsed into a valid score."""


def parse_judgement_response(text: str) -> tuple[JudgementResponse, str]:
    """Parse one raw judge reply, reporting which strategy succeeded."""
    try:
        return parse_json_response(text, JudgementResponse, "Judge response")
    except ResponseParseError as exc:
        raise JudgementParseError(str(exc), raw_response=exc.raw_response) from exc


class HostilityJudge:
    """Scores published debate messages on the 0-4 hostility scale.

    Independent of the moderator by design: a different model family (the
    anti-affinity requirement), and no knowledge of whether a message was
    reformulated. It scores text, not interventions.
    """

    def __init__(
        self,
        client: LLMClient,
        logger: JudgementLogger | None = None,
        system_prompt: str | None = None,
        runs_per_message: int = RUNS_PER_MESSAGE,
    ) -> None:
        if runs_per_message < 1:
            raise ValueError("runs_per_message must be at least 1.")

        self.client = client
        self.logger = logger
        self.system_prompt = (
            system_prompt if system_prompt is not None else load_system_prompt()
        )
        self.runs_per_message = runs_per_message
        self.system_prompt_sha256 = (
            prompt_sha256() if system_prompt is None else None
        )

    def judge_message(
        self,
        request: JudgementRequest,
        experiment_id: str = "",
        condition: str = "",
    ) -> JudgementRecord:
        """Score one message, repeated `runs_per_message` times.

        Returns the record with every run kept individually. Consistency
        figures are derived from those runs, never stored in their place.
        """
        user_message = build_user_message(request)

        runs = [
            self._single_run(user_message, run_index)
            for run_index in range(1, self.runs_per_message + 1)
        ]

        record = JudgementRecord(
            experiment_id=experiment_id,
            turn=request.turn,
            persona_id=request.persona_id,
            timestamp=datetime.now().astimezone().isoformat(),
            topic=request.topic,
            condition=condition,
            message=request.message,
            context_length=len(
                [m for m in request.context if m.turn < request.turn]
            ),
            runs=runs,
        )

        if self.logger is not None:
            self.logger.log_judgement(record)

        return record

    def _single_run(self, user_message: str, run_index: int) -> JudgementRun:
        """One evaluation of the message, with a single corrective retry."""
        raw_text, call_metadata = self.client.call(self.system_prompt, user_message)

        try:
            response, strategy = parse_judgement_response(raw_text)
        except JudgementParseError:
            response, call_metadata = self._retry_for_valid_json(
                user_message, call_metadata
            )
            strategy = STRATEGY_RETRY

        return JudgementRun(
            run_index=run_index,
            response=response,
            model_call={
                **call_metadata,
                "parse_strategy": strategy,
                "parse_recovery_used": strategy != STRATEGY_DIRECT,
                "system_prompt_sha256": self.system_prompt_sha256,
            },
        )

    def _retry_for_valid_json(
        self, user_message: str, first_call_metadata: dict
    ) -> tuple[JudgementResponse, dict]:
        """One corrective call after an unusable reply."""
        raw_text, retry_metadata = self.client.call(
            self.system_prompt, user_message + REPARSE_INSTRUCTION
        )
        merged = merge_call_metadata(first_call_metadata, retry_metadata)
        try:
            response, _ = parse_judgement_response(raw_text)
        except JudgementParseError as exc:
            exc.call_metadata = merged
            raise
        return response, merged


def judge_transcript(
    judge: HostilityJudge,
    topic: str,
    condition: str,
    transcript: list[Any],
    experiment_id: str = "",
    on_message: Any = None,
) -> list[JudgementRecord]:
    """Score every published message in one debate.

    `transcript` is a list of `PublishedMessage`. Each message is scored with
    the messages before it as context, mirroring what a reader would have seen.
    A failure on one message propagates: partial scoring of a debate would give
    an average over a biased subset of turns.
    """
    ordered = sorted(transcript, key=lambda m: m.turn)
    records: list[JudgementRecord] = []

    for index, message in enumerate(ordered):
        request = JudgementRequest(
            topic=topic,
            persona_id=message.persona_id,
            turn=message.turn,
            message=message.text,
            context=ordered[:index],
        )
        record = judge.judge_message(
            request, experiment_id=experiment_id, condition=condition
        )
        records.append(record)
        if on_message is not None:
            on_message(record)

    return records