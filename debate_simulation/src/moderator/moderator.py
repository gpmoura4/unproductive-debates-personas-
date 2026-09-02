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

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from llm.client import LLMClient
from llm.parsing import (
    STRATEGY_BLOCK,
    STRATEGY_DIRECT,
    STRATEGY_FENCE,
    STRATEGY_QUOTES,
    STRATEGY_RETRY,
    ResponseParseError,
    merge_call_metadata,
    parse_json_response,
)
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

class ModerationParseError(ResponseParseError):
    """The moderator's response could not be parsed into a valid verdict.

    Raised after every recovery strategy has failed, including the one retry
    call. Carries the raw text of the last response so the failure can be
    diagnosed from the log without re-running the call.
    """


def parse_moderation_response_with_strategy(
    text: str,
) -> tuple[ModerationResponse, str]:
    """Parse one raw reply, reporting which strategy succeeded.

    Tries, in order: the raw text (`direct`), the body of a markdown fence
    (`fence_stripped`), the outermost balanced `{...}` block (`block_extracted`).
    Raises `ModerationParseError` if none yields a valid response — the caller
    decides whether to retry with a correction.

    The strategy is returned because how often a model needs recovery is a
    finding about that model, not just an implementation detail: it is recorded
    on every log entry.
    """
    try:
        return parse_json_response(text, ModerationResponse, "Moderator response")
    except ResponseParseError as exc:
        raise ModerationParseError(str(exc), raw_response=exc.raw_response) from exc


def parse_moderation_response(text: str) -> ModerationResponse:
    """Parse one raw moderator reply into a validated response.

    Thin wrapper over `parse_moderation_response_with_strategy` for callers
    that do not need to know how the text was recovered.
    """
    response, _ = parse_moderation_response_with_strategy(text)
    return response


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

        try:
            response, strategy = parse_moderation_response_with_strategy(raw_text)
        except ModerationParseError:
            strategy = STRATEGY_RETRY
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
                )
                raise

        record = self._build_record(
            request=request,
            response=response,
            experiment_id=experiment_id,
            turn=turn,
            call_metadata=call_metadata,
            parse_strategy=strategy,
        )
        if self.logger is not None:
            self.logger.log_moderation(record)

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
        merged = merge_call_metadata(first_call_metadata, retry_metadata)
        # Merged first: a failure here must still report both calls, so the
        # log shows the real cost of the turn rather than only the first call.
        try:
            response = parse_moderation_response(raw_text)
        except ModerationParseError as exc:
            exc.call_metadata = merged
            raise
        return response, merged

    def consistency_warning(self, response: ModerationResponse) -> str | None:
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
        parse_strategy: str,
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
                "was_reformulated": response.requires_intervention,
                "published_source": (
                    "reformulation" if response.requires_intervention else "candidate"
                ),
            },
            model_call=self._model_call_metadata(call_metadata, parse_strategy),
            consistency_warning=self.consistency_warning(response),
        )

    def _log_failure(
        self,
        request: ModerationRequest,
        experiment_id: str,
        turn: int | None,
        call_metadata: dict,
        error: ModerationParseError,
    ) -> None:
        """Record an irrecoverable parse failure, then let the error propagate.

        Written through the logger so the turn is not silently missing: an
        absent file is indistinguishable from a turn that never ran. Logging
        must not mask the original failure, so an error while writing is
        suppressed — the ModerationParseError is the one that matters.
        """
        if self.logger is None:
            return

        # The retry attaches both calls' metadata to the exception; fall back
        # to the first call's when it is absent.
        metadata = error.call_metadata or call_metadata

        try:
            self.logger.log_failure(
                turn=turn if turn is not None else len(request.history) + 1,
                persona_id=request.persona_id,
                error=error,
                raw_response=error.raw_response,
                attempts=metadata.get("attempts"),
                request=request,
                model_call=self._model_call_metadata(metadata, STRATEGY_RETRY),
            )
        except Exception:  # noqa: BLE001 — never mask the parse failure
            pass

    def _model_call_metadata(
        self, call_metadata: dict, parse_strategy: str
    ) -> dict[str, Any]:
        """Call metadata plus the fields the record adds on top of it.

        `parse_recovery_used` is true whenever the reply needed anything beyond
        a direct parse — fence stripping and block extraction included, not
        only the retry call.
        """
        return {
            **call_metadata,
            "parse_strategy": parse_strategy,
            "parse_recovery_used": parse_strategy != STRATEGY_DIRECT,
            "system_prompt_sha256": self.system_prompt_sha256,
        }
