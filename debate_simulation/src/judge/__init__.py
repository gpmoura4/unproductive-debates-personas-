"""Hostility judge (Model C) — scores published messages on the 0-4 scale.

Independent of both debaters and moderator: a different model family, and no
knowledge of which messages were reformulated. Each message is scored several
times so intra-judge consistency can be measured.
"""

from judge.judge import (
    REPARSE_INSTRUCTION,
    HostilityJudge,
    JudgementParseError,
    judge_transcript,
    parse_judgement_response,
)
from judge.logger import JudgementLogger
from judge.prompt import (
    DEFAULT_SYSTEM_PROMPT_PATH,
    build_user_message,
    load_system_prompt,
    prompt_sha256,
)
from judge.schema import (
    RUNS_PER_MESSAGE,
    JudgementRecord,
    JudgementRequest,
    JudgementResponse,
    JudgementRun,
)

__all__ = [
    "DEFAULT_SYSTEM_PROMPT_PATH",
    "REPARSE_INSTRUCTION",
    "RUNS_PER_MESSAGE",
    "HostilityJudge",
    "JudgementLogger",
    "JudgementParseError",
    "JudgementRecord",
    "JudgementRequest",
    "JudgementResponse",
    "JudgementRun",
    "build_user_message",
    "judge_transcript",
    "load_system_prompt",
    "parse_judgement_response",
    "prompt_sha256",
]