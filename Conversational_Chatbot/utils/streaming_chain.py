from collections.abc import Iterator, Sequence
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from utils.history import format_messages_as_transcript
from utils.load_llm import get_llm_instance, get_model_candidates, is_transient_model_error

DEFAULT_SYSTEM_INSTRUCTION = (
    "You are a helpful assistant. Answer clearly and accurately based on the conversation."
)


def build_chat_prompt(system_instruction: str | None = None) -> ChatPromptTemplate:
    """
    Build the chat prompt with an optional runtime system instruction.

    :param system_instruction: Optional custom system prompt text.

    :returns prompt: Prompt template for the current turn.
    """
    instruction = (
        system_instruction.strip()
        if isinstance(system_instruction, str) and system_instruction.strip()
        else DEFAULT_SYSTEM_INSTRUCTION
    )
    return ChatPromptTemplate.from_messages(
        [
            ("system", instruction),
            (
                "human",
                "Conversation:\n{chat_transcript}\n\nWrite your next reply as the assistant.",
            ),
        ]
    )


def stream_chat_response(
    messages: Sequence[BaseMessage],
    *,
    system_instruction: str | None = None,
    max_history_messages: int | None = 24,
    temperature: float | None = None,
    disable_safety_filters: bool | None = None,
) -> Iterator[str]:
    """
    Stream plain-text tokens for the assistant reply, given full message history
    (including the latest user message).

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
            streaming=True,
            model_name=model_name,
            temperature=temperature,
            disable_safety_filters=disable_safety_filters,
        )
        chain = prompt | llm | StrOutputParser()
        has_streamed_chunk = False
        try:
            for chunk in chain.stream({"chat_transcript": transcript}):
                if isinstance(chunk, str) and chunk:
                    has_streamed_chunk = True
                    yield chunk
            return
        except Exception as err:  # noqa: BLE001 - model/provider errors are runtime-dependent
            errors.append(f"{model_name}: {err}")
            is_last_model = index == len(model_candidates) - 1
            # If partial text already reached the UI, switching models mid-response can
            # create duplicated/conflicting output. In that case we stop and ask user to retry.
            if has_streamed_chunk:
                raise RuntimeError(
                    "Streaming response was interrupted after partial output. "
                    "Use 'Retry last response' to regenerate the full answer cleanly. "
                    f"Last error from {model_name}: {err}"
                ) from err

            if is_last_model or not is_transient_model_error(err):
                break

    joined_errors = " | ".join(errors)
    raise RuntimeError(
        "All configured models failed before streaming any text. "
        f"Details: {joined_errors}"
    )
