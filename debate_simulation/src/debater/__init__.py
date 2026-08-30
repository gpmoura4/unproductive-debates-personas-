"""Debating agents — Layer 1 (persona identity) + Layer 2 (behavioral rules).

Produces the candidate messages the D5 moderator evaluates in the treatment
condition, and the messages published directly in the control condition.
"""

from debater.debater import Debater, DebaterError, clean_message
from debater.prompt import (
    DEFAULT_BEHAVIOR_PROMPT_PATH,
    build_system_prompt,
    build_user_message,
    load_behavior_prompt,
    load_persona_prompt,
    persona_prompt_path,
    prompt_sha256,
)

__all__ = [
    "DEFAULT_BEHAVIOR_PROMPT_PATH",
    "Debater",
    "DebaterError",
    "build_system_prompt",
    "build_user_message",
    "clean_message",
    "load_behavior_prompt",
    "load_persona_prompt",
    "persona_prompt_path",
    "prompt_sha256",
]
