import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser

from utils.history import format_messages_as_transcript
from utils.load_llm import get_llm_instance, get_model_candidates, is_transient_model_error
from utils.streaming_chain import build_chat_prompt

if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" not in os.environ:
    load_dotenv()


def run_chat_turn(
    messages: list[Any],
    *,
    system_instruction: str | None = None,
    max_history_messages: int | None = 24,
    temperature: float | None = None,
    disable_safety_filters: bool | None = None,
) -> str:
    """
    Non-streaming reply for the current conversation. `messages` may be BaseMessage
    objects or dicts with role/content (as in the simple Streamlit app).

    :param messages: Chat history messages.
    :param system_instruction: Optional custom system instruction.
    :param max_history_messages: Maximum recent messages to include in context.
    :param temperature: Optional generation temperature override.
    :param disable_safety_filters: Optional override for dangerous-content filtering.
    """
    transcript = format_messages_as_transcript(
        messages,
        max_messages=max_history_messages,
    )
    errors: list[str] = []
    model_candidates = get_model_candidates()
    prompt = build_chat_prompt(system_instruction)
    for index, model_name in enumerate(model_candidates):
        llm = get_llm_instance(
            streaming=False,
            model_name=model_name,
            temperature=temperature,
            disable_safety_filters=disable_safety_filters,
        )
        chain = prompt | llm | StrOutputParser()
        try:
            return chain.invoke({"chat_transcript": transcript})
        except Exception as err:  # noqa: BLE001 - model/provider errors are runtime-dependent
            errors.append(f"{model_name}: {err}")
            is_last_model = index == len(model_candidates) - 1
            if is_last_model or not is_transient_model_error(err):
                break

    joined_errors = " | ".join(errors)
    raise RuntimeError(
        "All configured models failed. Set GEMINI_MODEL/GEMINI_FALLBACK_MODELS in .env "
        f"or try again shortly. Details: {joined_errors}"
    )
