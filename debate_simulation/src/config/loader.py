"""Model profile configuration for the three experiment roles.

Loads `config/models.yaml` and resolves one profile (`smoke_test`, `local`,
`hybrid`, `api_only`) into typed `ModelConfig` objects for the debater,
moderator and judge.

Switching profiles is a one-line change: the CLI flag, the `DEBATE_PROFILE`
env var, or `default_profile` in the YAML.

API keys are never read here — this module only verifies that the required
env vars are set for the providers a profile actually uses. The key itself is
read by `llm.client.LLMClient` at call time.

Credentials may live in a `.env` file at the repo root or in
`debate_simulation/`; it is loaded into the environment on first use. A real
environment variable always wins over the file, and `.env` is gitignored.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Anchored to this file (src/config/loader.py -> debate_simulation/) so the
# default resolves the same from the repo root or from debate_simulation/.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "models.yaml"

PROFILE_ENV_VAR = "DEBATE_PROFILE"

ROLES = ("debater", "moderator", "judge")

# Providers that authenticate with a key. Ollama runs locally and needs none.
PROVIDERS_REQUIRING_KEY = frozenset({"openrouter"})

REQUIRED_ROLE_FIELDS = ("provider", "model", "base_url", "temperature", "max_tokens")

# Searched in order; every match is loaded, earlier files winning. Covers a
# .env beside the subproject and one at the repo root.
DOTENV_SEARCH_PATHS = (
    _PROJECT_ROOT / ".env",
    _PROJECT_ROOT.parent / ".env",
)

_dotenv_loaded = False


def load_dotenv(paths: tuple[Path, ...] = DOTENV_SEARCH_PATHS) -> list[Path]:
    """Load `KEY=value` lines from .env files into os.environ.

    Variables already present in the environment are never overwritten — an
    explicit `export` outranks the file. Supports `#` comments, blank lines, a
    leading `export `, and quoted values. Malformed lines are skipped rather
    than raising: a stray line should not block a run.

    Returns the files actually loaded. Idempotent across calls.
    """
    loaded: list[Path] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].lstrip()
            key, sep, value = line.partition("=")
            if not sep:
                continue
            key = key.strip()
            if not key:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            os.environ.setdefault(key, value)

        loaded.append(path)
    return loaded


def _ensure_dotenv_loaded() -> None:
    global _dotenv_loaded
    if not _dotenv_loaded:
        load_dotenv()
        _dotenv_loaded = True


class ConfigError(RuntimeError):
    """Raised when the model configuration is missing, malformed or unusable."""


class ConfigFileNotFoundError(ConfigError, FileNotFoundError):
    """Config file absent. Also a FileNotFoundError, so callers can catch either."""


class UnknownProfileError(ConfigError, ValueError):
    """Profile name not defined in the config. Also a ValueError."""


class MissingAPIKeyError(ConfigError):
    """A provider used by the profile needs an env var that is not set."""


@dataclass(frozen=True, slots=True)
class ModelConfig:
    role: str  # "debater" | "moderator" | "judge"
    provider: str  # "ollama" | "openrouter"
    model: str
    base_url: str
    api_key_env: str | None
    temperature: float
    max_tokens: int

    @property
    def requires_api_key(self) -> bool:
        return self.provider in PROVIDERS_REQUIRING_KEY


@dataclass(frozen=True, slots=True)
class ProfileConfig:
    name: str  # "smoke_test" | "local" | "hybrid" | "api_only"
    debater: ModelConfig
    moderator: ModelConfig
    judge: ModelConfig

    def roles(self) -> list[ModelConfig]:
        """The three role configs, in experiment order."""
        return [self.debater, self.moderator, self.judge]


def _build_model_config(role: str, raw: Any, profile_name: str) -> ModelConfig:
    if not isinstance(raw, dict):
        raise ConfigError(
            f"Profile '{profile_name}', role '{role}': expected a mapping of "
            f"settings, got {type(raw).__name__}."
        )

    missing = [f for f in REQUIRED_ROLE_FIELDS if raw.get(f) is None]
    if missing:
        raise ConfigError(
            f"Profile '{profile_name}', role '{role}': missing required "
            f"field(s): {', '.join(missing)}."
        )

    try:
        temperature = float(raw["temperature"])
        max_tokens = int(raw["max_tokens"])
    except (TypeError, ValueError) as e:
        raise ConfigError(
            f"Profile '{profile_name}', role '{role}': temperature must be a "
            f"number and max_tokens an integer ({e})."
        ) from None

    return ModelConfig(
        role=role,
        provider=str(raw["provider"]),
        model=str(raw["model"]),
        base_url=str(raw["base_url"]),
        api_key_env=raw.get("api_key_env"),
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _verify_api_keys(profile: ProfileConfig) -> None:
    """Check that env vars are set for providers this profile actually uses.

    Only the roles in this profile are checked — a `local` run must not fail
    because OPENROUTER_API_KEY is unset.
    """
    missing: list[str] = []
    for cfg in profile.roles():
        if not cfg.requires_api_key:
            continue
        if not cfg.api_key_env:
            raise ConfigError(
                f"Profile '{profile.name}', role '{cfg.role}': provider "
                f"'{cfg.provider}' requires an API key, but no 'api_key_env' "
                f"is configured."
            )
        if not os.environ.get(cfg.api_key_env):
            missing.append(f"{cfg.api_key_env} (role: {cfg.role}, provider: {cfg.provider})")

    if missing:
        unique_vars = sorted({m.split(" ")[0] for m in missing})
        raise MissingAPIKeyError(
            f"Profile '{profile.name}' needs API key environment variable(s) "
            f"that are not set:\n  - " + "\n  - ".join(missing) + "\n\n"
            f"Set them before running, e.g.:\n"
            + "\n".join(f"  export {v}=sk-or-..." for v in unique_vars)
            + f"\n\nOr put them in a .env file at {DOTENV_SEARCH_PATHS[1]} "
            f"(or {DOTENV_SEARCH_PATHS[0]}), one KEY=value per line."
        )


def load_profile(
    profile_name: str | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> ProfileConfig:
    """Load one model profile.

    Resolution order for `profile_name`:
    1. the `profile_name` argument, when given
    2. the DEBATE_PROFILE environment variable
    3. `default_profile` from the YAML

    Raises `ConfigFileNotFoundError` (a FileNotFoundError) when the file is
    missing, `UnknownProfileError` (a ValueError) when the profile does not
    exist — the message lists the available ones —, `MissingAPIKeyError` when a
    required env var is unset for a provider the profile uses, and
    `ConfigError` when the file is malformed.
    """
    _ensure_dotenv_loaded()

    config_path = Path(config_path)
    if not config_path.is_file():
        raise ConfigFileNotFoundError(
            f"Model configuration not found at: {config_path.resolve()}"
        )

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ConfigError(f"Could not parse {config_path.resolve()}: {e}") from None

    if not isinstance(raw, dict):
        raise ConfigError(
            f"{config_path.resolve()}: expected a top-level mapping with a "
            f"'profiles' key."
        )

    profiles = raw.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ConfigError(
            f"{config_path.resolve()}: no profiles defined under the "
            f"'profiles' key."
        )

    selected = profile_name or os.environ.get(PROFILE_ENV_VAR) or raw.get("default_profile")
    if not selected:
        raise ConfigError(
            f"No profile selected and no 'default_profile' set in "
            f"{config_path.resolve()}. Pass one explicitly, set "
            f"{PROFILE_ENV_VAR}, or add a default. "
            f"Available: {', '.join(sorted(profiles))}."
        )

    if selected not in profiles:
        raise UnknownProfileError(
            f"Unknown profile '{selected}'. Available profiles: "
            f"{', '.join(sorted(profiles))}."
        )

    profile_data = profiles[selected]
    if not isinstance(profile_data, dict):
        raise ConfigError(
            f"Profile '{selected}': expected a mapping of roles, got "
            f"{type(profile_data).__name__}."
        )

    missing_roles = [r for r in ROLES if r not in profile_data]
    if missing_roles:
        raise ConfigError(
            f"Profile '{selected}' is missing role(s): "
            f"{', '.join(missing_roles)}. Every profile must define all three: "
            f"{', '.join(ROLES)}."
        )

    profile = ProfileConfig(
        name=selected,
        **{role: _build_model_config(role, profile_data[role], selected) for role in ROLES},
    )

    _verify_api_keys(profile)
    return profile


def available_profiles(config_path: Path = DEFAULT_CONFIG_PATH) -> list[str]:
    """Names of the profiles defined in the config file."""
    config_path = Path(config_path)
    if not config_path.is_file():
        raise ConfigFileNotFoundError(
            f"Model configuration not found at: {config_path.resolve()}"
        )
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return sorted((raw.get("profiles") or {}).keys())
