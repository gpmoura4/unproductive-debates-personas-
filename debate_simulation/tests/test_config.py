"""Offline tests for the model profile loader.

No network calls: env vars are mocked with monkeypatch and only the YAML on
disk is read. These tests pin the profile contract that the experiment
depends on — provider per role, resolution order, and which credentials each
profile actually requires.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from config.loader import (
    PROFILE_ENV_VAR,
    ModelConfig,
    load_profile,
)

API_KEY_ENV = "OPENROUTER_API_KEY"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start every test from a known environment.

    DEBATE_PROFILE unset, API key present — tests that care about either one
    override it explicitly.
    """
    monkeypatch.delenv(PROFILE_ENV_VAR, raising=False)
    monkeypatch.setenv(API_KEY_ENV, "sk-or-test-key")


def _providers(profile) -> list[str]:
    return [cfg.provider for cfg in profile.roles()]


# --- 1-4: provider layout per profile -------------------------------------


def test_smoke_test_profile_is_all_free_openrouter() -> None:
    profile = load_profile("smoke_test")

    assert [type(c) for c in profile.roles()] == [ModelConfig] * 3
    assert _providers(profile) == ["openrouter"] * 3
    for cfg in profile.roles():
        assert cfg.model.endswith(":free"), (
            f"role {cfg.role} uses {cfg.model}, which is not a free-tier model"
        )


def test_local_profile_is_all_ollama() -> None:
    profile = load_profile("local")

    assert [type(c) for c in profile.roles()] == [ModelConfig] * 3
    assert _providers(profile) == ["ollama"] * 3


def test_hybrid_profile_runs_judge_on_ollama() -> None:
    profile = load_profile("hybrid")

    assert _providers(profile) == ["openrouter", "openrouter", "ollama"]
    assert profile.debater.provider == "openrouter"
    assert profile.moderator.provider == "openrouter"
    assert profile.judge.provider == "ollama"


def test_api_only_profile_is_all_openrouter() -> None:
    profile = load_profile("api_only")

    assert [type(c) for c in profile.roles()] == [ModelConfig] * 3
    assert _providers(profile) == ["openrouter"] * 3


# --- 5-7: profile resolution order ----------------------------------------


def test_no_argument_uses_default_profile_from_yaml() -> None:
    assert load_profile().name == "smoke_test"


def test_env_var_overrides_default_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PROFILE_ENV_VAR, "api_only")

    assert load_profile().name == "api_only"


def test_explicit_argument_overrides_env_var_and_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(PROFILE_ENV_VAR, "api_only")

    assert load_profile("hybrid").name == "hybrid"


# --- 8-9: error cases ------------------------------------------------------


def test_missing_config_file_raises_with_resolved_path(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.yaml"

    with pytest.raises(FileNotFoundError) as excinfo:
        load_profile("local", missing)

    assert str(missing.resolve()) in str(excinfo.value)


def test_unknown_profile_raises_listing_available_profiles() -> None:
    with pytest.raises(ValueError) as excinfo:
        load_profile("does_not_exist")

    message = str(excinfo.value)
    assert "does_not_exist" in message
    for name in ("smoke_test", "local", "hybrid", "api_only"):
        assert name in message, f"error should list available profile {name!r}"


# --- 10-12: API key verification is scoped to the providers actually used --


def test_smoke_test_without_api_key_names_the_missing_env_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(API_KEY_ENV, raising=False)

    with pytest.raises(Exception) as excinfo:
        load_profile("smoke_test")

    assert API_KEY_ENV in str(excinfo.value)


def test_local_profile_does_not_require_openrouter_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(API_KEY_ENV, raising=False)

    profile = load_profile("local")

    assert profile.name == "local"
    assert all(cfg.api_key_env is None for cfg in profile.roles())


def test_hybrid_requires_openrouter_key_but_no_ollama_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The OpenRouter roles need the key...
    monkeypatch.delenv(API_KEY_ENV, raising=False)
    with pytest.raises(Exception) as excinfo:
        load_profile("hybrid")
    assert API_KEY_ENV in str(excinfo.value)

    # ...and with it set, the Ollama judge needs no credential of its own.
    monkeypatch.setenv(API_KEY_ENV, "sk-or-test-key")
    profile = load_profile("hybrid")
    assert profile.judge.api_key_env is None
    assert not profile.judge.requires_api_key
