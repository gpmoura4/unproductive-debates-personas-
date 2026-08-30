"""Recovering a JSON object from a model reply.

Shared by the moderator and the judge: both instruct the model to answer with
JSON only, and both face the same deviations — markdown fences, and reasoning
models that narrate before emitting the object.

Which strategy succeeded is reported alongside the parsed value, because how
often a model needs recovery is a finding about that model, not an
implementation detail.
"""

from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

# How the JSON was recovered. `direct` means the model obeyed the output
# contract; anything else means recovery was needed.
STRATEGY_DIRECT = "direct"
STRATEGY_FENCE = "fence_stripped"
STRATEGY_BLOCK = "block_extracted"
STRATEGY_RETRY = "retry_call"

# Matches a ```json ... ``` or ``` ... ``` fence wrapping the whole payload.
_FENCE_PATTERN = re.compile(
    r"^\s*```(?:json)?\s*\n(?P<body>.*?)\n?\s*```\s*$",
    re.DOTALL | re.IGNORECASE,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


class ResponseParseError(RuntimeError):
    """A model reply could not be parsed into a valid response.

    Carries the raw text so the failure can be diagnosed from the log without
    re-running the call.
    """

    def __init__(self, message: str, raw_response: str) -> None:
        super().__init__(message)
        self.raw_response = raw_response
        # Set by callers that retry, so a failure record reports both calls.
        self.call_metadata: dict | None = None


def strip_fences(text: str) -> str | None:
    """The body of a markdown code fence, or None if the text is not fenced."""
    match = _FENCE_PATTERN.match(text)
    return match.group("body") if match else None


def extract_outermost_object(text: str) -> str | None:
    """The outermost {...} block, or None when there is no balanced object.

    Scans for the first `{` and its matching `}`, tracking nesting depth and
    skipping braces inside strings. This is what recovers a verdict from a
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


def parse_json_response(
    text: str, model: type[ModelT], what: str = "Response"
) -> tuple[ModelT, str]:
    """Parse one raw reply into `model`, reporting which strategy succeeded.

    Tries, in order: the raw text, the body of a markdown fence, the outermost
    balanced `{...}` block. Raises `ResponseParseError` if none yields a valid
    response — the caller decides whether to retry with a correction.

    Schema violations are treated the same as malformed JSON from the caller's
    point of view (both mean the reply is unusable), but they fail immediately
    rather than trying later strategies: those only narrow the same text, so
    valid JSON that breaks the contract cannot be rescued by them.
    """
    strategies: list[tuple[str, str]] = [(STRATEGY_DIRECT, text)]
    for name, extract in (
        (STRATEGY_FENCE, strip_fences),
        (STRATEGY_BLOCK, extract_outermost_object),
    ):
        extracted = extract(text)
        if extracted is not None and all(extracted != seen for _, seen in strategies):
            strategies.append((name, extracted))

    last_error: Exception | None = None
    for strategy, candidate in strategies:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue

        try:
            return model.model_validate(payload), strategy
        except ValidationError as exc:
            raise ResponseParseError(
                f"{what} did not satisfy the output contract: {exc}",
                raw_response=text,
            ) from exc

    raise ResponseParseError(
        f"{what} was not valid JSON: {last_error}", raw_response=text
    )


def merge_call_metadata(first: dict, second: dict) -> dict:
    """Combine two calls into one unit's metadata.

    Latency and attempts are summed rather than replaced: a turn that needed a
    reparse really did cost two calls, and recording only the second would
    understate the experiment's cost.
    """
    merged = dict(second)
    merged["calls"] = 2
    merged["attempts"] = first.get("attempts", 1) + second.get("attempts", 1)
    merged["latency_ms"] = first.get("latency_ms", 0) + second.get("latency_ms", 0)
    return merged