"""Incremental persistence of moderation records — the traceability backbone.

Layout, one directory per run:

    experiments/
    └── {experiment_id}/
        ├── manifest.json
        └── moderation/
            ├── turn_001_persona_1.json
            └── turn_002_persona_2.json

Each record is written the moment its turn completes, so a run interrupted at
turn 11 keeps turns 1-10 (requirement 8.3 of the experiment design). Records
are never overwritten: a collision gets a numeric suffix, because a log that
can silently lose a turn is not a log.

Two things live here and nowhere else:

- **MatrAIx provenance** (`matraix_source`, `matraix_id`) — the internal link
  from a debate back to the dataset rows that produced its personas. It is
  copied into the manifest and MUST NEVER reach a prompt sent to an LLM; the
  political-lean blinding depends on that separation.
- **Prompt digests** — SHA-256 of the exact prompt files used, which is what
  proves after the fact which frozen prompt version produced a run.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Anchored to this file (src/moderator/logger.py -> debate_simulation/) so the
# default resolves the same from the repo root or from debate_simulation/.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_BASE_DIR = _PROJECT_ROOT / "experiments"

DEFAULT_PERSONA_METADATA_PATH = (
    _PROJECT_ROOT / "outputs" / "prompts" / "personas" / "persona_metadata.json"
)

BEHAVIOR_PROMPT_PATH = (
    _PROJECT_ROOT / "prompts" / "debate behavior" / "debate behavior.txt"
)

# Pole -> directory holding that pole's Layer 1 prompts.
POLE_DIRECTORIES = {"left": "polo_esquerda", "right": "polo_direita"}

CONDITIONS = ("control", "treatment")

EXPERIMENT_ID_TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"


def slugify(text: str) -> str:
    """Lowercase, hyphen-separated form of a topic, safe as a path segment."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")
    if not slug:
        raise ValueError(f"Topic {text!r} produced an empty slug.")
    return slug


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _relative_to_repo(path: Path) -> str:
    """Repo-relative path string, for a manifest that survives being moved."""
    path = Path(path).resolve()
    try:
        return str(path.relative_to(_PROJECT_ROOT.parent))
    except ValueError:
        return str(path)


def build_experiment_id(
    topic: str,
    pair_id: str,
    condition: str,
    timestamp: datetime | None = None,
) -> str:
    """`{YYYYMMDD-HHMMSS}_{topic_slug}_{pair_id}_{condition}`.

    The timestamp makes re-runs of the same cell distinct directories rather
    than collisions, so an aborted run is never silently mixed with its retry.
    """
    if condition not in CONDITIONS:
        raise ValueError(
            f"Unknown condition {condition!r}; expected one of {CONDITIONS}."
        )
    stamp = (timestamp or datetime.now().astimezone()).strftime(
        EXPERIMENT_ID_TIMESTAMP_FORMAT
    )
    return f"{stamp}_{slugify(topic)}_{pair_id}_{condition}"


def load_persona_metadata(
    path: Path = DEFAULT_PERSONA_METADATA_PATH,
) -> list[dict[str, Any]]:
    """The 20 persona metadata entries, as written by the generation script."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Persona metadata not found at: {path}. Run "
            "scripts/00_generate_persona_prompts.py first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _find_persona(
    metadata: list[dict[str, Any]], pole: str, persona_index: int
) -> dict[str, Any]:
    for entry in metadata:
        if entry.get("pole") == pole and entry.get("persona_index") == persona_index:
            return entry
    raise ValueError(
        f"No persona with pole={pole!r} and persona_index={persona_index} in "
        "the metadata."
    )


def _persona_manifest_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Manifest block for one persona, including its dataset provenance.

    `prompt_file` is derived from pole and index rather than stored, since the
    generation script names the files by that convention.
    """
    pole = entry["pole"]
    directory = POLE_DIRECTORIES.get(pole)
    if directory is None:
        raise ValueError(f"Unknown pole {pole!r}; expected one of {sorted(POLE_DIRECTORIES)}.")

    prompt_path = (
        _PROJECT_ROOT
        / "outputs"
        / "prompts"
        / "personas"
        / directory
        / f"persona_{entry['persona_index']:02d}.txt"
    )
    return {
        "prompt_file": _relative_to_repo(prompt_path),
        "pole": pole,
        "persona_index": entry["persona_index"],
        # Provenance: internal only, never sent to a model.
        "matraix_source": entry.get("matraix_source"),
        "matraix_id": entry.get("matraix_id"),
        "prompt_version": entry.get("prompt_version"),
        "blinded_attributes": entry.get("blinded_attributes"),
    }


def _model_manifest_entry(model_config: Any, role_label: str) -> dict[str, Any]:
    return {
        "role": role_label,
        "model": model_config.model,
        "provider": model_config.provider,
        "temperature": model_config.temperature,
        "max_tokens": model_config.max_tokens,
    }


def build_manifest(
    experiment_id: str,
    topic: str,
    pair_id: str,
    condition: str,
    profile: Any,
    persona_1_index: int,
    persona_2_index: int,
    moderator_prompt_path: Path,
    planned_turns: int,
    seed: int | None = None,
    intervention_threshold: int = 2,
    persona_metadata_path: Path = DEFAULT_PERSONA_METADATA_PATH,
    persona_1_pole: str = "left",
    persona_2_pole: str = "right",
) -> dict[str, Any]:
    """Assemble the manifest so the debate loop never builds it by hand.

    `profile` is a `config.loader.ProfileConfig`. Both debaters share one model
    by design (difference in tone must come from the persona, not the model),
    so the manifest records a single `debaters` entry.

    In the control condition there is no moderator: its model and prompt
    digest are recorded as None, which is what distinguishes a control
    manifest from a treatment one at read time.
    """
    metadata = load_persona_metadata(persona_metadata_path)
    is_treatment = condition == "treatment"

    manifest: dict[str, Any] = {
        "experiment_id": experiment_id,
        "created_at": datetime.now().astimezone().isoformat(),
        "condition": condition,
        "topic": topic,
        "pair_id": pair_id,
        "personas": {
            "persona_1": _persona_manifest_entry(
                _find_persona(metadata, persona_1_pole, persona_1_index)
            ),
            "persona_2": _persona_manifest_entry(
                _find_persona(metadata, persona_2_pole, persona_2_index)
            ),
        },
        "models": {
            "debaters": _model_manifest_entry(profile.debater, "A"),
            "moderator": (
                _model_manifest_entry(profile.moderator, "B") if is_treatment else None
            ),
        },
        "profile": getattr(profile, "name", None),
        "moderator_prompt_file": (
            _relative_to_repo(moderator_prompt_path) if is_treatment else None
        ),
        "moderator_prompt_sha256": (
            _sha256(moderator_prompt_path) if is_treatment else None
        ),
        "behavior_prompt_file": _relative_to_repo(BEHAVIOR_PROMPT_PATH),
        "behavior_prompt_sha256": _sha256(BEHAVIOR_PROMPT_PATH),
        "intervention_threshold": intervention_threshold,
        "planned_turns": planned_turns,
        "seed": seed,
    }
    return manifest


def find_runs(
    topic: str | None = None,
    pair_id: str | None = None,
    condition: str | None = None,
    base_dir: Path = DEFAULT_BASE_DIR,
) -> list[str]:
    """Existing experiment_ids, newest last, optionally filtered.

    Lets a runner find a previous attempt at the same cell before starting a
    new one. Filtering is by the components encoded in the directory name, so
    it does not need to open every manifest.
    """
    base_dir = Path(base_dir)
    if not base_dir.is_dir():
        return []

    wanted = (
        slugify(topic) if topic else None,
        pair_id,
        condition,
    )
    runs: list[str] = []
    for path in sorted(base_dir.iterdir()):
        if not path.is_dir():
            continue
        parts = path.name.split("_")
        if len(parts) != 4:
            continue
        _, run_topic, run_pair, run_condition = parts
        found = (run_topic, run_pair, run_condition)
        if all(w is None or w == f for w, f in zip(wanted, found)):
            runs.append(path.name)
    return runs


def _serialize(value: Any) -> Any:
    """JSON-ready form of dataclasses, pydantic models and enums."""
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


class ModerationLogger:
    """Writes one JSON file per moderated turn, plus a manifest per run."""

    def __init__(
        self,
        experiment_id: str,
        manifest: dict[str, Any],
        base_dir: Path = DEFAULT_BASE_DIR,
    ) -> None:
        self.experiment_id = experiment_id
        self.manifest = manifest
        self.base_dir = Path(base_dir)
        self.experiment_dir = self.base_dir / experiment_id
        self.moderation_dir = self.experiment_dir / "moderation"

    @property
    def manifest_path(self) -> Path:
        return self.experiment_dir / "manifest.json"

    def write_manifest(self) -> Path:
        """Create the run directory and write the manifest.

        Rewriting the manifest of an existing run is refused: it describes the
        conditions the already-written records were produced under, so
        replacing it would misattribute them.
        """
        self.moderation_dir.mkdir(parents=True, exist_ok=True)
        if self.manifest_path.exists():
            raise FileExistsError(
                f"Manifest already exists at {self.manifest_path}; refusing to "
                "overwrite the description of an existing run."
            )
        self._write_json(self.manifest_path, self.manifest)
        return self.manifest_path

    def log_moderation(self, record: Any) -> Path:
        """Persist one completed moderation. Returns the file written."""
        payload = {
            "experiment_id": record.experiment_id or self.experiment_id,
            "turn": record.turn,
            "persona_id": record.persona_id,
            "timestamp": record.timestamp,
            "topic": record.topic,
            "input": self._input_block(record.input),
            "moderation": _serialize(record.moderation),
            "resolution": record.resolution,
            "model_call": record.model_call,
            "consistency_warning": record.consistency_warning,
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
        attempts: int | None = None,
        request: Any = None,
        model_call: dict[str, Any] | None = None,
    ) -> Path:
        """Persist an irrecoverable failure, so the turn is not simply absent.

        Written before the exception propagates. A missing file would be
        indistinguishable from a turn that never ran.
        """
        payload = {
            "experiment_id": self.experiment_id,
            "turn": turn,
            "persona_id": persona_id,
            "timestamp": datetime.now().astimezone().isoformat(),
            "status": "FAILED",
            "input": self._input_block(request) if request is not None else None,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
            "raw_response": raw_response,
            "attempts": attempts,
            "model_call": model_call,
        }
        path = self._next_available_path(turn, persona_id, failed=True)
        self._write_json(path, payload)
        return path

    # --- reading back, for resumption -------------------------------------

    def exists(self) -> bool:
        """Whether this run has already been started on disk."""
        return self.manifest_path.exists()

    def read_manifest(self) -> dict[str, Any]:
        """The manifest of an existing run, for verifying it matches this one."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"No manifest at {self.manifest_path}.")
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def completed_turns(self) -> set[tuple[int, str]]:
        """`(turn, persona_id)` pairs already logged successfully.

        Failure records are excluded: a turn that failed was not completed, and
        must be re-run rather than skipped. Suffixed duplicates collapse into
        the same pair, so a re-run turn is not counted twice.
        """
        completed: set[tuple[int, str]] = set()
        for path in self._record_paths():
            parsed = self._parse_record_filename(path.stem)
            if parsed is not None:
                completed.add(parsed)
        return completed

    def last_completed_turn(self) -> int:
        """Highest turn number logged, or 0 for a run with no records yet."""
        turns = [turn for turn, _ in self.completed_turns()]
        return max(turns, default=0)

    def failed_turns(self) -> set[tuple[int, str]]:
        """`(turn, persona_id)` pairs whose moderation failed irrecoverably."""
        failed: set[tuple[int, str]] = set()
        for path in self._record_paths(failed=True):
            parsed = self._parse_record_filename(
                path.stem[: -len("_FAILED")]
                if path.stem.endswith("_FAILED")
                else path.stem
            )
            if parsed is not None:
                failed.add(parsed)
        return failed

    def load_published_history(self) -> list[dict[str, Any]]:
        """The published transcript reconstructed from the logged records.

        Returns `{"turn", "persona_id", "text"}` in turn order, where `text` is
        what was actually published — the reformulation when the moderator
        intervened. This is what lets a resumed debate continue from the real
        transcript rather than re-running earlier turns.
        """
        by_turn: dict[int, dict[str, Any]] = {}
        for path in self._record_paths():
            payload = json.loads(path.read_text(encoding="utf-8"))
            turn = payload.get("turn")
            if turn is None:
                continue
            # A re-run turn wins: later suffixes sort after the original.
            by_turn[turn] = {
                "turn": turn,
                "persona_id": payload.get("persona_id"),
                "text": payload.get("resolution", {}).get("published_text", ""),
            }
        return [by_turn[turn] for turn in sorted(by_turn)]

    def _record_paths(self, failed: bool = False) -> list[Path]:
        """Record files in stable order; successes and failures never mix."""
        if not self.moderation_dir.is_dir():
            return []
        paths = sorted(self.moderation_dir.glob("turn_*.json"))
        return [p for p in paths if ("_FAILED" in p.stem) is failed]

    @staticmethod
    def _parse_record_filename(stem: str) -> tuple[int, str] | None:
        """`turn_003_persona_1` and `turn_003_persona_1_2` -> `(3, "persona_1")`."""
        match = re.match(r"^turn_(\d+)_(persona_\d+)(?:_\d+)?$", stem)
        if match is None:
            return None
        return int(match.group(1)), match.group(2)

    # --- writing helpers --------------------------------------------------

    def _input_block(self, request: Any) -> dict[str, Any]:
        """The candidate plus the exact history the moderator saw.

        The snapshot costs disk but makes each record auditable on its own,
        without replaying the debate — required for the human audit of 30
        pairs.
        """
        history = sorted(request.history, key=lambda m: m.turn)
        return {
            "candidate": request.candidate,
            "history_length": len(history),
            "history_snapshot": [
                {"turn": m.turn, "persona_id": m.persona_id, "text": m.text}
                for m in history
            ],
        }

    def _next_available_path(
        self, turn: int, persona_id: str, failed: bool = False
    ) -> Path:
        """A path that does not exist yet, suffixing on collision.

        Never overwrites: a repeated turn+persona means something was re-run,
        and both attempts are data.
        """
        suffix = "_FAILED" if failed else ""
        stem = f"turn_{turn:03d}_{persona_id}{suffix}"
        path = self.moderation_dir / f"{stem}.json"

        counter = 2
        while path.exists():
            path = self.moderation_dir / f"{stem}_{counter}.json"
            counter += 1
        return path

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
