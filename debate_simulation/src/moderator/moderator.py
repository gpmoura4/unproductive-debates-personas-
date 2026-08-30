"""Moderation orchestration.

Ties prompt assembly, the LLM call and logging together: takes a
`ModerationRequest`, returns the validated `ModerationResponse`, and records a
`ModerationRecord` for the log.

The LLM transport is the shared `llm.client.LLMClient`, configured for the
moderator role by the active profile (`config/models.yaml`) — this module does
not know which model or provider it is talking to.

Failure policy: an irrecoverable parse failure raises. This module never
returns a default or placeholder verdict, because a fabricated "no hostility"
result would enter the experiment as if the model had judged the message.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from llm.client import LLMClient
from moderator.prompt import build_user_message, load_system_prompt, prompt_sha256
from moderator.schema import (
    INTERVENTION_THRESHOLD,
    ModerationRecord,
    ModerationRequest,
    ModerationResponse,
)

if TYPE_CHECKING:
    # Not yet implemented; imported for typing only so this module stays
    # importable while logger.py is still a placeholder.
    from moderator.logger import ModerationLogger

# Appended to the user message on the single reparse attempt. Kept blunt and
# short: the model already received the full OUTPUT FORMAT section, so this is
# a correction, not a re-explanation.
REPARSE_INSTRUCTION = (
    "\n\nYour previous response was not valid JSON. Respond with ONLY the "
    "JSON object."
)

# Matches a ```json ... ``` or ``` ... ``` fence wrapping the whole payload.
_FENCE_PATTERN = re.compile(
    r"^\s*```(?:json)?\s*\n(?P<body>.*?)\n?\s*```\s*$",
    re.DOTALL | re.IGNORECASE,
)


class ModerationParseError(RuntimeError):
    """The moderator's response could not be parsed into a valid verdict.

    Raised after every recovery strategy has failed, including the one retry
    call. Carries the raw text of the last response so the failure can be
    diagnosed from the log without re-running the call.
    """

    def __init__(self, message: str, raw_response: str) -> None:
        super().__init__(message)
        self.raw_response = raw_response


def _strip_fences(text: str) -> str | None:
    """The body of a markdown code fence, or None if the text is not fenced."""
    match = _FENCE_PATTERN.match(text)
    return match.group("body") if match else None


def _extract_outermost_object(text: str) -> str | None:
    """The outermost {...} block, or None when there is no balanced object.

    Scans for the first `{` and its matching `}`, tracking nesting depth and
    skipping braces inside strings. This is what recovers the verdict from a
    reasoning model that narrates before emitting JSON.
    """
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(text)):
        char = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return None


def parse_moderation_response(text: str) -> ModerationResponse:
    """Parse one raw moderator reply into a validated response.

    Tries, in order: the raw text, the body of a markdown fence, the outermost
    balanced `{...}` block. Raises `ModerationParseError` if none yields a
    valid response — the caller decides whether to retry with a correction.

    Schema violations are treated the same as malformed JSON: both mean the
    reply is unusable, and both are recoverable by asking again.
    """
    candidates = [text]
    for extract in (_strip_fences, _extract_outermost_object):
        extracted = extract(text)
        if extracted is not None and extracted not in candidates:
            candidates.append(extracted)

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue

        try:
            return ModerationResponse.model_validate(payload)
        except ValidationError as exc:
            # Valid JSON that breaks the contract: no later strategy will help,
            # since they only ever narrow the same text.
            raise ModerationParseError(
                f"Moderator response did not satisfy the output contract: {exc}",
                raw_response=text,
            ) from exc

    raise ModerationParseError(
        f"Moderator response was not valid JSON: {last_error}",
        raw_response=text,
    )


class D5Moderator:
    """Prospective moderator: evaluates a candidate message before publication.

    `system_prompt` defaults to the D5 prompt on disk, loaded verbatim.
    `intervention_threshold` mirrors the prompt's own rule (hostility >= 2);
    it is used for the consistency check recorded on each record, never to
    override the model's `requires_intervention`.
    """

    def __init__(
        self,
        client: LLMClient,
        logger: ModerationLogger | None = None,
        system_prompt: str | None = None,
        intervention_threshold: int = INTERVENTION_THRESHOLD,
    ) -> None:
        self.client = client
        self.logger = logger
        self.system_prompt = (
            system_prompt if system_prompt is not None else load_system_prompt()
        )
        self.intervention_threshold = intervention_threshold
        # Recorded on every record so a run can be traced back to the exact
        # prompt text. None for an injected prompt: hashing the file would
        # misidentify what was actually sent. Computed once — the prompt does
        # not change during a run.
        self.system_prompt_sha256 = (
            prompt_sha256() if system_prompt is None else None
        )

    def moderate(
        self,
        request: ModerationRequest,
        experiment_id: str = "",
        turn: int | None = None,
    ) -> ModerationResponse:
        """Evaluate one candidate message.

        Calls the moderator model, parses the verdict, records it, and returns
        the validated response. One reparse attempt is made when the first
        reply is unusable; if that also fails, a failure record is written and
        `ModerationParseError` propagates. Never returns a placeholder verdict.

        `experiment_id` and `turn` only identify the record for the log; the
        moderation itself does not depend on them.
        """
        user_message = build_user_message(request)
        raw_text, call_metadata = self.client.call(self.system_prompt, user_message)

        parse_recovery_used = False
        try:
            response = parse_moderation_response(raw_text)
        except ModerationParseError as first_error:
            parse_recovery_used = True
            try:
                response, call_metadata = self._retry_for_valid_json(
                    user_message, call_metadata
                )
            except ModerationParseError as retry_error:
                self._log_failure(
                    request=request,
                    experiment_id=experiment_id,
                    turn=turn,
                    call_metadata=call_metadata,
                    error=retry_error,
                    first_error=first_error,
                )
                raise

        record = self._build_record(
            request=request,
            response=response,
            experiment_id=experiment_id,
            turn=turn,
            call_metadata=call_metadata,
            parse_recovery_used=parse_recovery_used,
        )
        if self.logger is not None:
            self.logger.write(record)

        return response

    def resolve_published_text(
        self, request: ModerationRequest, response: ModerationResponse
    ) -> str:
        """The text that actually gets published this turn.

        The reformulation when the moderator intervened, the original candidate
        otherwise. This is what the debate loop appends to the transcript and
        what the opponent replies to — the step that propagates the D5 effect.
        """
        if response.requires_intervention:
            if response.reformulation is None:
                # Unreachable via a validated response; guards against a
                # hand-built one silently publishing an empty message.
                raise ValueError(
                    "requires_intervention is true but no reformulation is "
                    "available to publish."
                )
            return response.reformulation
        return request.candidate

    def _retry_for_valid_json(
        self, user_message: str, first_call_metadata: dict
    ) -> tuple[ModerationResponse, dict]:
        """One corrective call after an unusable reply.

        Returns the parsed response and merged call metadata. Any
        `ModerationParseError` from this second attempt propagates to the
        caller, which writes the failure record.
        """
        raw_text, retry_metadata = self.client.call(
            self.system_prompt, user_message + REPARSE_INSTRUCTION
        )
        response = parse_moderation_response(raw_text)

        merged = dict(retry_metadata)
        merged["calls"] = 2
        merged["attempts"] = first_call_metadata.get("attempts", 1) + retry_metadata.get(
            "attempts", 1
        )
        merged["latency_ms"] = first_call_metadata.get("latency_ms", 0) + retry_metadata.get(
            "latency_ms", 0
        )
        return response, merged

    def _consistency_warning(self, response: ModerationResponse) -> str | None:
        """A warning when score and intervention decision disagree.

        The model's decision stands either way — the disagreement is data about
        model behavior, not an error to correct.
        """
        if response.requires_intervention == (
            response.hostility_level >= self.intervention_threshold
        ):
            return None

        if response.requires_intervention:
            return (
                f"Intervened at hostility_level {response.hostility_level}, "
                f"below the threshold of {self.intervention_threshold}."
            )
        return (
            f"Did not intervene at hostility_level {response.hostility_level}, "
            f"at or above the threshold of {self.intervention_threshold}."
        )

    def _build_record(
        self,
        request: ModerationRequest,
        response: ModerationResponse,
        experiment_id: str,
        turn: int | None,
        call_metadata: dict,
        parse_recovery_used: bool,
    ) -> ModerationRecord:
        published_text = self.resolve_published_text(request, response)
        return ModerationRecord(
            experiment_id=experiment_id,
            turn=turn if turn is not None else len(request.history) + 1,
            persona_id=request.persona_id,
            timestamp=datetime.now(UTC).isoformat(),
            topic=request.topic,
            input=request,
            moderation=response,
            resolution={
                "published_text": published_text,
                "intervened": response.requires_intervention,
                "published_source": (
                    "reformulation" if response.requires_intervention else "candidate"
                ),
            },
            model_call=self._model_call_metadata(call_metadata, parse_recovery_used),
            consistency_warning=self._consistency_warning(response),
        )

    def _log_failure(
        self,
        request: ModerationRequest,
        experiment_id: str,
        turn: int | None,
        call_metadata: dict,
        error: ModerationParseError,
        first_error: ModerationParseError,
    ) -> None:
        """Record an irrecoverable parse failure, then let the error propagate.

        Written through the logger's failure path so the turn is not silently
        missing from the log. Uses `write_failure` when the logger provides it
        (step 5); a logger without it is tolerated so this module stays usable
        before the logger is finished.
        """
        if self.logger is None:
            return

        write_failure = getattr(self.logger, "write_failure", None)
        if write_failure is None:
            return

        write_failure(
            {
                "experiment_id": experiment_id,
                "turn": turn if turn is not None else len(request.history) + 1,
                "persona_id": request.persona_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "topic": request.topic,
                "candidate": request.candidate,
                "error": str(error),
                "first_error": str(first_error),
                "raw_response": error.raw_response,
                "model_call": self._model_call_metadata(
                    call_metadata, parse_recovery_used=True
                ),
            }
        )

    def _model_call_metadata(
        self, call_metadata: dict, parse_recovery_used: bool
    ) -> dict[str, Any]:
        """Call metadata plus the fields the record adds on top of it."""
        return {
            **call_metadata,
            "parse_recovery_used": parse_recovery_used,
            "system_prompt_sha256": self.system_prompt_sha256,
        }
