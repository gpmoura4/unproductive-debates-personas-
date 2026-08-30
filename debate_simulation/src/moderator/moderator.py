"""Moderation orchestration.

Ties prompt assembly, the LLM call and logging together: takes a
`ModerationRequest`, returns the text to publish (candidate or reformulation)
plus the `ModerationRecord` for the log.

The LLM transport is the shared `llm.client.LLMClient`, configured for the
moderator role by the active profile (`config/models.yaml`) — this module does
not know which model or provider it is talking to.

Placeholder — the `moderate()` body is implemented in a later step.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from llm.client import LLMClient
from moderator.prompt import load_system_prompt
from moderator.schema import INTERVENTION_THRESHOLD

if TYPE_CHECKING:
    # Not yet implemented; imported for typing only so this module stays
    # importable while logger.py is still a placeholder.
    from moderator.logger import ModerationLogger


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
