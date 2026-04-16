import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory

load_dotenv()

# "gemini-pro" is deprecated; use a current model (override with GEMINI_MODEL in .env).
_DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_FALLBACK_MODELS = os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.0-flash")
_DEFAULT_TEMPERATURE_FALLBACK = 0.2


def _env_flag(name: str, *, default: bool = False) -> bool:
    """
    Parse a boolean environment variable.

    :param name: Environment variable name.
    :param default: Value to return when unset.

    :returns value: Parsed flag value.
    """
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _coerce_temperature(value: float | str | None, *, fallback: float) -> float:
    """
    Clamp model temperature into the Gemini-supported range [0.0, 2.0].

    :param value: Raw value from UI or env.
    :param fallback: Safe fallback when parsing fails.

    :returns temperature: Clamped float value.
    """
    try:
        parsed = float(value) if value is not None else float(fallback)
    except (TypeError, ValueError):
        parsed = float(fallback)
    return max(0.0, min(2.0, parsed))


_DEFAULT_TEMPERATURE = _coerce_temperature(
    os.getenv("GEMINI_TEMPERATURE"),
    fallback=_DEFAULT_TEMPERATURE_FALLBACK,
)
_DEFAULT_DISABLE_SAFETY_FILTERS = _env_flag(
    "GEMINI_DISABLE_SAFETY_FILTERS",
    default=False,
)

_llm_cache: dict[tuple[bool, str, float, bool], ChatGoogleGenerativeAI] = {}


def is_api_key_configured() -> bool:
    """
    Return whether at least one Gemini API key is configured.

    :returns has_key: True when a key is available in env.
    """
    return bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))


def get_model_candidates() -> list[str]:
    """
    Return ordered model candidates for failover attempts.

    :returns model_names: Ordered unique model names (primary first).
    """
    raw_models = [_DEFAULT_MODEL, *_FALLBACK_MODELS.split(",")]
    normalized_models = [model.strip() for model in raw_models if model.strip()]
    unique_models = list(dict.fromkeys(normalized_models))
    return unique_models


def get_default_temperature() -> float:
    """
    Return the configured default temperature.

    :returns temperature: Default model temperature in [0.0, 2.0].
    """
    return _DEFAULT_TEMPERATURE


def get_default_disable_safety_filters() -> bool:
    """
    Return whether safety filters are disabled by default.

    :returns disable_filters: True when explicit unfiltered mode is enabled.
    """
    return _DEFAULT_DISABLE_SAFETY_FILTERS


def is_transient_model_error(error: Exception) -> bool:
    """
    Return whether an exception looks transient and retryable.

    :param error: Raised model invocation exception.

    :returns is_transient: True when a fallback retry should be attempted.
    """
    error_text = str(error).lower()
    transient_markers = (
        "429",
        "rate limit",
        "resource exhausted",
        "overloaded",
        "congestion",
        "temporarily unavailable",
        "deadline exceeded",
        "timeout",
        "unavailable",
    )
    return any(marker in error_text for marker in transient_markers)


def get_llm_instance(
    *,
    streaming: bool = False,
    model_name: str | None = None,
    temperature: float | None = None,
    disable_safety_filters: bool | None = None,
) -> ChatGoogleGenerativeAI:
    """
    Return a cached ChatGoogleGenerativeAI client.

    :param streaming: Whether this client should stream token chunks.
    :param model_name: Optional explicit model name.
    :param temperature: Optional generation temperature override.
    :param disable_safety_filters: Optional override for dangerous-content filter behavior.

    :returns llm: Cached model client for the selected model and mode.
    """
    if not is_api_key_configured():
        raise RuntimeError(
            "No API key found. Create a .env file in the project folder with:\n"
            "  GOOGLE_API_KEY=your_key_here\n"
            "(GEMINI_API_KEY also works.)"
        )

    selected_model = model_name or _DEFAULT_MODEL
    selected_temperature = _coerce_temperature(
        temperature,
        fallback=_DEFAULT_TEMPERATURE,
    )
    selected_disable_safety_filters = (
        _DEFAULT_DISABLE_SAFETY_FILTERS
        if disable_safety_filters is None
        else bool(disable_safety_filters)
    )

    key = (
        streaming,
        selected_model,
        round(selected_temperature, 3),
        selected_disable_safety_filters,
    )
    if key not in _llm_cache:
        client_kwargs: dict[str, object] = {
            "model": selected_model,
            "streaming": streaming,
            "temperature": selected_temperature,
        }
        if selected_disable_safety_filters:
            client_kwargs["safety_settings"] = {
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

        _llm_cache[key] = ChatGoogleGenerativeAI(
            **client_kwargs,
        )
    return _llm_cache[key]
