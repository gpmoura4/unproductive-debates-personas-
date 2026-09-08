"""Persistence of judgement records, alongside the moderation log.

    experiments/{experiment_id}/
    ├── manifest.json
    ├── transcript.json
    ├── moderation/
    └── judgements/
        ├── turn_001_persona_1.json
        └── turn_002_persona_2.json

Same guarantees as the moderation log: written per message as it completes,
never overwritten, and readable back so a judging pass can resume. Every run is
stored individually — the consistency summary is derived alongside them, not
instead of them, so a change of aggregation method never requires re-judging.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from moderator.logger import DEFAULT_BASE_DIR

JUDGEMENTS_DIRNAME = "judgements"


class JudgementLogger:
    """Writes one JSON file per judged message."""

    def __init__(
        self,
        experiment_id: str,
        base_dir: Path = DEFAULT_BASE_DIR,
    ) -> None:
        self.experiment_id = experiment_id
        self.base_dir = Path(base_dir)
        self.experiment_dir = self.base_dir / experiment_id
        self.judgements_dir = self.experiment_dir / JUDGEMENTS_DIRNAME

    def log_judgement(self, record: Any) -> Path:
        """Persist one message's runs plus the derived summary."""
        payload = {
            "experiment_id": record.experiment_id or self.experiment_id,
            "turn": record.turn,
            "persona_id": record.persona_id,
            "timestamp": record.timestamp,
            "topic": record.topic,
            "condition": record.condition,
            "message": record.message,
            "context_length": record.context_length,
            "runs": [
                {
                    "run_index": run.run_index,
                    "hostility_level": run.response.hostility_level,
                    "pathologies_detected": [
                        p.value for p in run.response.pathologies_detected
                    ],
                    "justification": run.response.justification,
                    "targets_person": run.response.targets_person,
                    "model_call": run.model_call,
                }
                for run in record.runs
            ],
            "summary": record.summary(),
        }
        path = self._next_available_path(record.turn, record.persona_id)
        self._write_json(path, payload)
        return path

    def log_failure(
        self,
        turn: int,
        persona_id: str,
        error: BaseException,
        raw_response: str | None = None,
        run_index: int | None = None,
        model_call: dict[str, Any] | None = None,
    ) -> Path:
        """Persist an irrecoverable judging failure, so the message is not
        silently absent from the log."""
        payload = {
            "experiment_id": self.experiment_id,
            "turn": turn,
            "persona_id": persona_id,
            "timestamp": datetime.now().astimezone().isoformat(),
            "status": "FAILED",
            "run_index": run_index,
            "error": {"type": type(error).__name__, "message": str(error)},
            "raw_response": raw_response,
            "model_call": model_call,
        }
        path = self._next_available_path(turn, persona_id, failed=True)
        self._write_json(path, payload)
        return path

    # --- reading back, for resumption -------------------------------------

    def judged_messages(self) -> set[tuple[int, str]]:
        """`(turn, persona_id)` pairs already scored successfully."""
        judged: set[tuple[int, str]] = set()
        for path in self._record_paths():
            parsed = self._parse_record_filename(path.stem)
            if parsed is not None:
                judged.add(parsed)
        return judged

    def load_scores(self) -> list[dict[str, Any]]:
        """Per-message scores in turn order, for analysis.

        Returns the derived summary plus identity, not the full runs — callers
        needing individual runs read the files directly.
        """
        scores: list[dict[str, Any]] = []
        for path in self._record_paths():
            payload = json.loads(path.read_text(encoding="utf-8"))
            scores.append(
                {
                    "turn": payload.get("turn"),
                    "persona_id": payload.get("persona_id"),
                    "condition": payload.get("condition"),
                    **payload.get("summary", {}),
                }
            )
        return sorted(scores, key=lambda s: (s["turn"] or 0))

    def _record_paths(self, failed: bool = False) -> list[Path]:
        if not self.judgements_dir.is_dir():
            return []
        paths = sorted(self.judgements_dir.glob("turn_*.json"))
        return [p for p in paths if ("_FAILED" in p.stem) is failed]

    @staticmethod
    def _parse_record_filename(stem: str) -> tuple[int, str] | None:
        match = re.match(r"^turn_(\d+)_(persona_\d+)(?:_\d+)?$", stem)
        if match is None:
            return None
        return int(match.group(1)), match.group(2)

    def _next_available_path(
        self, turn: int, persona_id: str, failed: bool = False
    ) -> Path:
        """A path that does not exist yet, suffixing on collision."""
        suffix = "_FAILED" if failed else ""
        stem = f"turn_{turn:03d}_{persona_id}{suffix}"
        path = self.judgements_dir / f"{stem}.json"

        counter = 2
        while path.exists():
            path = self.judgements_dir / f"{stem}_{counter}.json"
            counter += 1
        return path

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )