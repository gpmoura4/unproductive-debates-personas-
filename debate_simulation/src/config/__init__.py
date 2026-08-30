"""Model profile configuration for the debate simulation experiment."""

from config.loader import (
    DEFAULT_CONFIG_PATH,
    PROFILE_ENV_VAR,
    ConfigError,
    ConfigFileNotFoundError,
    MissingAPIKeyError,
    ModelConfig,
    ProfileConfig,
    UnknownProfileError,
    available_profiles,
    load_profile,
)

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "PROFILE_ENV_VAR",
    "ConfigError",
    "ConfigFileNotFoundError",
    "MissingAPIKeyError",
    "ModelConfig",
    "ProfileConfig",
    "UnknownProfileError",
    "available_profiles",
    "load_profile",
]
