"""Tests for experiment logging.

Everything writes to tmp_path — no test touches the real experiments/ tree.
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from config.loader import ModelConfig, ProfileConfig
from moderator.logger import (
    ModerationLogger,
    build_experiment_id,
    build_manifest,
    find_runs,
    slugify,
)
from moderator.moderator import D5Moderator, ModerationParseError
from moderator.prompt import DEFAULT_SYSTEM_PROMPT_PATH
from moderator.schema import ModerationRecord, ModerationRequest, ModerationResponse, PublishedMessage

from tests.test_moderator import (
    CLEAN_VERDICT,
    HOSTILE_VERDICT,
    FakeClient,
    make_request,
)


def make_profile() -> ProfileConfig:
    def model(role: str, name: str, temperature: float) -> ModelConfig:
        return ModelConfig(
            role=role,
            provider="openrouter",
            model=name,
            base_url="https://openrouter.ai/api/v1",
            api_key_env="OPENROUTER_API_KEY",
            temperature=temperature,
            max_tokens=400,
        )

    return ProfileConfig(
        name="smoke_test",
        debater=model("debater", "model-a", 0.7),
        moderator=model("moderator", "model-b", 0.2),
        judge=model("judge", "model-c", 0.0),
    )


def make_record(turn: int = 3, persona_id: str = "persona_1") -> ModerationRecord:
    return ModerationRecord(
        experiment_id="exp-1",
        turn=turn,
        persona_id=persona_id,
        timestamp="2026-08-30T14:30:12-03:00",
        topic="Gun Ownership",
        input=make_request(),
        moderation=ModerationResponse.model_validate(HOSTILE_VERDICT),
        resolution={
            "published_text": HOSTILE_VERDICT["reformulation"],
            "was_reformulated": True,
            "published_source": "reformulation",
        },
        model_call={"model": "model-b", "latency_ms": 1834, "attempts": 1},
        consistency_warning=None,
    )


def make_logger(tmp_path, manifest=None) -> ModerationLogger:
    return ModerationLogger(
        experiment_id="exp-1",
        manifest=manifest or {"experiment_id": "exp-1"},
        base_dir=tmp_path,
    )


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


# --- experiment_id ---------------------------------------------------------


def test_slugify_normalizes_topic():
    assert slugify("Gun Ownership") == "gun-ownership"
    assert slugify("  Drug   Legalization  ") == "drug-legalization"


def test_slugify_rejects_empty_result():
    with pytest.raises(ValueError):
        slugify("!!!")


def test_experiment_id_follows_specified_format():
    stamp = datetime(2026, 8, 29, 14, 30, 12)
    experiment_id = build_experiment_id(
        "Gun Ownership", "pair-00", "treatment", timestamp=stamp
    )
    assert experiment_id == "20260829-143012_gun-ownership_pair-00_treatment"


def test_experiment_id_rejects_unknown_condition():
    with pytest.raises(ValueError):
        build_experiment_id("Abortion", "pair-01", "placebo")


# --- manifest --------------------------------------------------------------


def test_manifest_carries_provenance_and_digests():
    manifest = build_manifest(
        experiment_id="exp-1",
        topic="Gun Ownership",
        pair_id="pair-00",
        condition="treatment",
        profile=make_profile(),
        persona_1_index=0,
        persona_2_index=0,
        moderator_prompt_path=DEFAULT_SYSTEM_PROMPT_PATH,
        planned_turns=12,
        seed=42,
    )

    assert manifest["condition"] == "treatment"
    assert manifest["planned_turns"] == 12
    assert manifest["seed"] == 42
    assert manifest["intervention_threshold"] == 2

    persona_1 = manifest["personas"]["persona_1"]
    assert persona_1["matraix_id"]  # provenance present
    assert persona_1["matraix_source"]
    assert "polo_esquerda" in persona_1["prompt_file"]
    assert manifest["personas"]["persona_2"]["pole"] == "right"

    assert len(manifest["moderator_prompt_sha256"]) == 64
    assert len(manifest["behavior_prompt_sha256"]) == 64
    assert manifest["models"]["debaters"]["model"] == "model-a"
    assert manifest["models"]["moderator"]["model"] == "model-b"


def test_control_manifest_has_no_moderator():
    manifest = build_manifest(
        experiment_id="exp-1",
        topic="Abortion",
        pair_id="pair-00",
        condition="control",
        profile=make_profile(),
        persona_1_index=0,
        persona_2_index=0,
        moderator_prompt_path=DEFAULT_SYSTEM_PROMPT_PATH,
        planned_turns=12,
    )

    assert manifest["models"]["moderator"] is None
    assert manifest["moderator_prompt_sha256"] is None
    # The behavior prompt applies in both conditions.
    assert manifest["behavior_prompt_sha256"] is not None


def test_manifest_rejects_unknown_persona_index():
    with pytest.raises(ValueError):
        build_manifest(
            experiment_id="exp-1",
            topic="Abortion",
            pair_id="pair-00",
            condition="control",
            profile=make_profile(),
            persona_1_index=99,
            persona_2_index=0,
            moderator_prompt_path=DEFAULT_SYSTEM_PROMPT_PATH,
            planned_turns=12,
        )


def test_write_manifest_creates_layout(tmp_path):
    logger = make_logger(tmp_path, manifest={"experiment_id": "exp-1", "seed": 42})
    path = logger.write_manifest()

    assert path == tmp_path / "exp-1" / "manifest.json"
    assert (tmp_path / "exp-1" / "moderation").is_dir()
    assert read(path)["seed"] == 42


def test_write_manifest_refuses_to_overwrite(tmp_path):
    logger = make_logger(tmp_path)
    logger.write_manifest()

    with pytest.raises(FileExistsError):
        logger.write_manifest()


def test_written_manifest_has_full_structure_and_real_digests(tmp_path):
    """Item 16: the manifest on disk, not just the dict."""
    manifest = build_manifest(
        experiment_id="exp-1",
        topic="Gun Ownership",
        pair_id="pair-00",
        condition="treatment",
        profile=make_profile(),
        persona_1_index=0,
        persona_2_index=0,
        moderator_prompt_path=DEFAULT_SYSTEM_PROMPT_PATH,
        planned_turns=12,
        seed=42,
    )
    logger = ModerationLogger("exp-1", manifest, base_dir=tmp_path)
    payload = read(logger.write_manifest())

    for key in (
        "experiment_id",
        "created_at",
        "condition",
        "topic",
        "pair_id",
        "personas",
        "models",
        "moderator_prompt_file",
        "moderator_prompt_sha256",
        "behavior_prompt_file",
        "behavior_prompt_sha256",
        "intervention_threshold",
        "planned_turns",
        "seed",
    ):
        assert key in payload, f"manifest is missing {key!r}"

    for digest_key in ("moderator_prompt_sha256", "behavior_prompt_sha256"):
        digest = payload[digest_key]
        assert digest and len(digest) == 64
        assert digest != "0" * 64

    assert set(payload["personas"]) == {"persona_1", "persona_2"}
    assert payload["personas"]["persona_1"]["matraix_id"]


# --- per-turn records ------------------------------------------------------


def test_record_filename_is_zero_padded(tmp_path):
    logger = make_logger(tmp_path)
    path = logger.log_moderation(make_record(turn=3, persona_id="persona_1"))

    assert path.name == "turn_003_persona_1.json"
    assert path.parent == tmp_path / "exp-1" / "moderation"


def test_record_contains_every_specified_block(tmp_path):
    logger = make_logger(tmp_path)
    payload = read(logger.log_moderation(make_record()))

    assert payload["turn"] == 3
    assert payload["persona_id"] == "persona_1"
    assert payload["topic"] == "Gun Ownership"
    assert payload["moderation"]["hostility_level"] == 3
    assert payload["moderation"]["pathologies_detected"] == [
        "rhetoric_of_incomprehension"
    ]
    assert payload["resolution"]["was_reformulated"] is True
    assert payload["model_call"]["latency_ms"] == 1834
    assert payload["consistency_warning"] is None


def test_record_stores_history_snapshot(tmp_path):
    """Each record must be auditable without replaying the debate."""
    logger = make_logger(tmp_path)
    payload = read(logger.log_moderation(make_record()))

    assert payload["input"]["candidate"] == "You are a moron."
    assert payload["input"]["history_length"] == 1
    assert payload["input"]["history_snapshot"] == [
        {"turn": 1, "persona_id": "persona_1", "text": "Opening."}
    ]


def test_history_snapshot_is_ordered_by_turn(tmp_path):
    record = make_record()
    record.input = ModerationRequest(
        topic="Gun Ownership",
        persona_id="persona_2",
        history=[
            PublishedMessage(turn=2, persona_id="persona_2", text="Second."),
            PublishedMessage(turn=1, persona_id="persona_1", text="First."),
        ],
        candidate="Third.",
    )
    logger = make_logger(tmp_path)
    snapshot = read(logger.log_moderation(record))["input"]["history_snapshot"]

    assert [m["turn"] for m in snapshot] == [1, 2]


def test_pathologies_serialize_as_strings(tmp_path):
    """The enum must land in JSON as its string value, not a repr."""
    logger = make_logger(tmp_path)
    raw = logger.log_moderation(make_record()).read_text(encoding="utf-8")

    assert "rhetoric_of_incomprehension" in raw
    assert "Pathology." not in raw


# --- idempotency -----------------------------------------------------------


def test_repeated_turn_suffixes_instead_of_overwriting(tmp_path):
    logger = make_logger(tmp_path)
    first = logger.log_moderation(make_record())
    second = logger.log_moderation(make_record())
    third = logger.log_moderation(make_record())

    assert first.name == "turn_003_persona_1.json"
    assert second.name == "turn_003_persona_1_2.json"
    assert third.name == "turn_003_persona_1_3.json"
    assert first.exists() and second.exists()


def test_distinct_personas_do_not_collide(tmp_path):
    logger = make_logger(tmp_path)
    a = logger.log_moderation(make_record(turn=3, persona_id="persona_1"))
    b = logger.log_moderation(make_record(turn=3, persona_id="persona_2"))

    assert a.name != b.name


# --- failure records -------------------------------------------------------


def test_failure_record_is_written_with_diagnosis(tmp_path):
    logger = make_logger(tmp_path)
    error = ModerationParseError("not JSON", raw_response="I refuse.")
    path = logger.log_failure(
        turn=4,
        persona_id="persona_2",
        error=error,
        raw_response="I refuse.",
        attempts=2,
        request=make_request(),
    )

    assert path.name == "turn_004_persona_2_FAILED.json"
    payload = read(path)
    assert payload["status"] == "FAILED"
    assert payload["error"]["type"] == "ModerationParseError"
    assert payload["error"]["message"] == "not JSON"
    assert payload["raw_response"] == "I refuse."
    assert payload["attempts"] == 2
    assert payload["input"]["candidate"] == "You are a moron."


def test_failure_record_tolerates_absent_raw_response(tmp_path):
    logger = make_logger(tmp_path)
    path = logger.log_failure(
        turn=1, persona_id="persona_1", error=RuntimeError("connection lost")
    )

    payload = read(path)
    assert payload["raw_response"] is None
    assert payload["input"] is None
    assert payload["error"]["type"] == "RuntimeError"


def test_failure_records_also_suffix(tmp_path):
    logger = make_logger(tmp_path)
    error = ModerationParseError("bad", raw_response="x")
    first = logger.log_failure(turn=4, persona_id="persona_2", error=error)
    second = logger.log_failure(turn=4, persona_id="persona_2", error=error)

    assert first.name == "turn_004_persona_2_FAILED.json"
    assert second.name == "turn_004_persona_2_FAILED_2.json"


# --- wiring into D5Moderator ----------------------------------------------


def test_moderate_writes_a_record_to_disk(tmp_path):
    logger = make_logger(tmp_path)
    logger.write_manifest()
    moderator = D5Moderator(
        client=FakeClient(json.dumps(HOSTILE_VERDICT)),
        logger=logger,
        system_prompt="test prompt",
    )

    moderator.moderate(make_request(), experiment_id="exp-1", turn=2)

    files = list((tmp_path / "exp-1" / "moderation").glob("*.json"))
    assert len(files) == 1
    assert read(files[0])["resolution"]["was_reformulated"] is True


def test_moderate_writes_failure_record_then_raises(tmp_path):
    logger = make_logger(tmp_path)
    logger.write_manifest()
    moderator = D5Moderator(
        client=FakeClient("garbage", "still garbage"),
        logger=logger,
        system_prompt="test prompt",
    )

    with pytest.raises(ModerationParseError):
        moderator.moderate(make_request(), experiment_id="exp-1", turn=2)

    files = list((tmp_path / "exp-1" / "moderation").glob("*.json"))
    assert len(files) == 1
    assert files[0].name.endswith("_FAILED.json")
    assert read(files[0])["raw_response"] == "still garbage"


def test_reading_back_ignores_a_run_that_never_started(tmp_path):
    logger = make_logger(tmp_path)

    assert logger.exists() is False
    assert logger.completed_turns() == set()
    assert logger.last_completed_turn() == 0
    assert logger.load_published_history() == []


def test_completed_turns_reports_what_is_on_disk(tmp_path):
    logger = make_logger(tmp_path)
    logger.log_moderation(make_record(turn=1, persona_id="persona_1"))
    logger.log_moderation(make_record(turn=2, persona_id="persona_2"))

    assert logger.completed_turns() == {(1, "persona_1"), (2, "persona_2")}
    assert logger.last_completed_turn() == 2
    assert logger.exists() is False  # no manifest written in this test


def test_failed_turns_are_not_counted_as_completed(tmp_path):
    """A failed turn must be re-run, not skipped on resume."""
    logger = make_logger(tmp_path)
    logger.log_moderation(make_record(turn=1, persona_id="persona_1"))
    logger.log_failure(
        turn=2,
        persona_id="persona_2",
        error=ModerationParseError("bad", raw_response="x"),
    )

    assert logger.completed_turns() == {(1, "persona_1")}
    assert logger.failed_turns() == {(2, "persona_2")}
    assert logger.last_completed_turn() == 1


def test_rerun_turn_counts_once(tmp_path):
    logger = make_logger(tmp_path)
    logger.log_moderation(make_record(turn=3, persona_id="persona_1"))
    logger.log_moderation(make_record(turn=3, persona_id="persona_1"))

    assert logger.completed_turns() == {(3, "persona_1")}


def test_published_history_reconstructs_the_transcript(tmp_path):
    """Resuming needs what was published, not what was proposed."""
    logger = make_logger(tmp_path)
    logger.log_moderation(make_record(turn=2, persona_id="persona_2"))
    logger.log_moderation(make_record(turn=1, persona_id="persona_1"))

    history = logger.load_published_history()
    assert [m["turn"] for m in history] == [1, 2]
    # The reformulation, not the hostile candidate.
    assert history[0]["text"] == HOSTILE_VERDICT["reformulation"]
    assert "moron" not in history[0]["text"]


def test_read_manifest_round_trips(tmp_path):
    logger = make_logger(tmp_path, manifest={"experiment_id": "exp-1", "seed": 42})
    logger.write_manifest()

    assert logger.exists() is True
    assert logger.read_manifest()["seed"] == 42


def test_read_manifest_raises_when_absent(tmp_path):
    with pytest.raises(FileNotFoundError):
        make_logger(tmp_path).read_manifest()


def test_find_runs_filters_by_cell(tmp_path):
    for name in (
        "20260830-100000_gun-ownership_pair-00_control",
        "20260830-110000_gun-ownership_pair-00_treatment",
        "20260830-120000_abortion_pair-01_treatment",
    ):
        (tmp_path / name).mkdir()

    assert len(find_runs(base_dir=tmp_path)) == 3
    assert find_runs(topic="Gun Ownership", base_dir=tmp_path) == [
        "20260830-100000_gun-ownership_pair-00_control",
        "20260830-110000_gun-ownership_pair-00_treatment",
    ]
    assert find_runs(condition="treatment", pair_id="pair-01", base_dir=tmp_path) == [
        "20260830-120000_abortion_pair-01_treatment"
    ]
    assert find_runs(topic="Drug Legalization", base_dir=tmp_path) == []


def test_find_runs_tolerates_an_absent_directory(tmp_path):
    assert find_runs(base_dir=tmp_path / "nope") == []


def test_resume_skips_completed_and_redoes_failed(tmp_path):
    """The resumption contract the debate loop will rely on."""
    logger = make_logger(tmp_path)
    logger.log_moderation(make_record(turn=1, persona_id="persona_1"))
    logger.log_moderation(make_record(turn=2, persona_id="persona_2"))
    logger.log_failure(
        turn=3, persona_id="persona_1", error=RuntimeError("timeout")
    )

    planned = [(1, "persona_1"), (2, "persona_2"), (3, "persona_1"), (4, "persona_2")]
    pending = [t for t in planned if t not in logger.completed_turns()]

    assert pending == [(3, "persona_1"), (4, "persona_2")]


def test_clean_verdict_publishes_candidate_in_record(tmp_path):
    logger = make_logger(tmp_path)
    moderator = D5Moderator(
        client=FakeClient(json.dumps(CLEAN_VERDICT)),
        logger=logger,
        system_prompt="test prompt",
    )

    moderator.moderate(make_request(candidate="A civil point."), turn=2)

    payload = read(next((tmp_path / "exp-1" / "moderation").glob("*.json")))
    assert payload["resolution"]["was_reformulated"] is False
    assert payload["resolution"]["published_text"] == "A civil point."
