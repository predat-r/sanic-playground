import os
from dataclasses import dataclass

from dotenv import load_dotenv


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "liquid/lfm-2.5-2.6b:free"
DEFAULT_MAX_INPUT_BYTES = 8 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 180.0
MODEL_MAX_COMPLETION_TOKENS = 8_192
DEFAULT_MAX_OUTPUT_TOKENS = 8_192


class ConfigurationError(RuntimeError):
    """Raised when required application configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    openrouter_api_key: str
    openrouter_model: str = DEFAULT_MODEL
    openrouter_base_url: str = OPENROUTER_BASE_URL
    openrouter_http_referer: str | None = None
    openrouter_app_title: str | None = None
    max_input_bytes: int = DEFAULT_MAX_INPUT_BYTES
    ai_timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS

    @classmethod
    def from_environment(cls) -> "Settings":
        load_dotenv()

        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ConfigurationError("OPENROUTER_API_KEY is required")

        return cls(
            openrouter_api_key=api_key,
            openrouter_model=os.getenv(
                "OPENROUTER_MODEL", DEFAULT_MODEL
            ).strip(),
            openrouter_base_url=os.getenv(
                "OPENROUTER_BASE_URL", OPENROUTER_BASE_URL
            ).rstrip("/"),
            openrouter_http_referer=_optional_env("OPENROUTER_HTTP_REFERER"),
            openrouter_app_title=_optional_env("OPENROUTER_APP_TITLE"),
            max_input_bytes=_positive_int_env(
                "PRESENTATION_MAX_INPUT_BYTES", DEFAULT_MAX_INPUT_BYTES
            ),
            ai_timeout_seconds=_positive_float_env(
                "OPENROUTER_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS
            ),
            max_output_tokens=_bounded_int_env(
                "OPENROUTER_MAX_OUTPUT_TOKENS",
                DEFAULT_MAX_OUTPUT_TOKENS,
                MODEL_MAX_COMPLETION_TOKENS,
            ),
        )


def _optional_env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _positive_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc

    if value <= 0:
        raise ConfigurationError(f"{name} must be greater than zero")
    return value


def _positive_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a number") from exc

    if value <= 0:
        raise ConfigurationError(f"{name} must be greater than zero")
    return value


def _bounded_int_env(name: str, default: int, maximum: int) -> int:
    value = _positive_int_env(name, default)
    if value > maximum:
        raise ConfigurationError(f"{name} must not exceed {maximum}")
    return value
