"""D5 Participatory Moderator — prospective moderation of debate messages.

Evaluates each candidate message before publication and, above the hostility
threshold, returns a non-hostile reformulation preserving the argument. Used
only in the TREATMENT condition of the experiment.
"""

from moderator.moderator import (
    D5Moderator,
    ModerationParseError,
    parse_moderation_response,
)
from moderator.prompt import (
    DEFAULT_SYSTEM_PROMPT_PATH,
    build_user_message,
    load_system_prompt,
    prompt_sha256,
)
from moderator.schema import (
    HOSTILITY_MAX,
    HOSTILITY_MIN,
    INTERVENTION_THRESHOLD,
    ModerationRecord,
    ModerationRequest,
    ModerationResponse,
    Pathology,
    PublishedMessage,
)

__all__ = [
    "DEFAULT_SYSTEM_PROMPT_PATH",
    "HOSTILITY_MAX",
    "HOSTILITY_MIN",
    "INTERVENTION_THRESHOLD",
    "D5Moderator",
    "ModerationParseError",
    "ModerationRecord",
    "ModerationRequest",
    "ModerationResponse",
    "Pathology",
    "PublishedMessage",
    "build_user_message",
    "load_system_prompt",
    "parse_moderation_response",
    "prompt_sha256",
]
