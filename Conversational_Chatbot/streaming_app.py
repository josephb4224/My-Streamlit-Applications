import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from utils.chat_store import (
    append_session_message,
    clear_session,
    create_session_id,
    delete_last_message,
    delete_last_assistant_message,
    get_session_message_counts,
    initialize_chat_store,
    list_session_ids,
    load_session_messages,
)
from utils.copy_button import render_copy_button
from utils.export import export_messages_as_json, export_messages_as_markdown
from utils.load_llm import (
    get_default_disable_safety_filters,
    get_default_temperature,
    get_model_candidates,
    is_api_key_configured,
)
from utils.presets import SYSTEM_INSTRUCTION_PRESETS
from utils.streaming_chain import DEFAULT_SYSTEM_INSTRUCTION, stream_chat_response
from utils.ui_accessibility import (
    apply_accessibility_styles,
    initialize_accessibility_state,
    render_accessibility_controls,
)

st.set_page_config(page_title="Conversational Bot!")
st.title("Conversational Chatbot 💬")

if not is_api_key_configured():
    st.error(
        "Missing **GOOGLE_API_KEY** (or **GEMINI_API_KEY**). Add it to a `.env` file "
        "in this project folder, then restart Streamlit."
    )
    st.stop()

initialize_chat_store()
initialize_accessibility_state()
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = create_session_id()

sidebar_sessions = list_session_ids()
if st.session_state.chat_session_id not in sidebar_sessions:
    sidebar_sessions.insert(0, st.session_state.chat_session_id)

st.sidebar.header("Chat Controls")
selected_session_id = st.sidebar.selectbox(
    "Conversation",
    options=sidebar_sessions,
    index=sidebar_sessions.index(st.session_state.chat_session_id),
)
if selected_session_id != st.session_state.chat_session_id:
    st.session_state.chat_session_id = selected_session_id
    st.session_state.messages = [
        AIMessage(content=message["content"]) if message["role"] == "assistant" else HumanMessage(content=message["content"])
        for message in load_session_messages(selected_session_id)
    ]
    st.rerun()

if st.sidebar.button("New conversation", use_container_width=True):
    st.session_state.chat_session_id = create_session_id()
    st.session_state.messages = []
    st.rerun()

if st.sidebar.button("Clear current conversation", use_container_width=True):
    clear_session(st.session_state.chat_session_id)
    st.session_state.messages = []
    st.rerun()

if st.sidebar.button("Retry last response", use_container_width=True):
    can_retry = (
        len(st.session_state.messages) >= 2
        and isinstance(st.session_state.messages[-1], AIMessage)
        and isinstance(st.session_state.messages[-2], HumanMessage)
    )
    if can_retry:
        st.session_state.messages.pop()
        delete_last_assistant_message(st.session_state.chat_session_id)
        st.session_state.retry_requested = True
        st.rerun()
    else:
        st.sidebar.info("Retry requires the latest turn to be user -> assistant.")

st.sidebar.caption("Model failover order")
st.sidebar.code(" -> ".join(get_model_candidates()))

if "system_instruction" not in st.session_state:
    st.session_state.system_instruction = DEFAULT_SYSTEM_INSTRUCTION
if "temperature" not in st.session_state:
    st.session_state.temperature = float(get_default_temperature())
if "max_history_messages" not in st.session_state:
    st.session_state.max_history_messages = 24
if "disable_safety_filters" not in st.session_state:
    st.session_state.disable_safety_filters = bool(get_default_disable_safety_filters())
if "system_prompt_preset_name" not in st.session_state:
    st.session_state.system_prompt_preset_name = "Balanced assistant"

preset_names = list(SYSTEM_INSTRUCTION_PRESETS.keys())
if st.session_state.system_prompt_preset_name not in preset_names:
    st.session_state.system_prompt_preset_name = preset_names[0]

st.sidebar.subheader("Generation")
temperature_value = min(max(float(st.session_state.temperature), 0.0), 2.0)
context_window_value = min(max(int(st.session_state.max_history_messages), 4), 60)
selected_preset = st.sidebar.selectbox(
    "System prompt preset",
    options=preset_names,
    index=preset_names.index(st.session_state.system_prompt_preset_name),
    help="Quickly switch behavior before editing the custom instruction text.",
)
st.session_state.system_prompt_preset_name = selected_preset
if st.sidebar.button("Apply selected preset", use_container_width=True):
    st.session_state.system_instruction = SYSTEM_INSTRUCTION_PRESETS[selected_preset]
    st.rerun()

st.session_state.temperature = st.sidebar.slider(
    "Temperature",
    min_value=0.0,
    max_value=2.0,
    value=temperature_value,
    step=0.05,
    help="Lower = more focused/deterministic. Higher = more creative/varied.",
)
st.session_state.max_history_messages = st.sidebar.slider(
    "Context window (messages)",
    min_value=4,
    max_value=60,
    value=context_window_value,
    step=2,
    help="How many recent messages are sent to the model each turn.",
)
st.session_state.system_instruction = st.sidebar.text_area(
    "System instruction",
    value=str(st.session_state.system_instruction),
    height=120,
    help="Steers response style/behavior for this browser session.",
)
st.session_state.disable_safety_filters = st.sidebar.checkbox(
    "Disable dangerous-content safety filter",
    value=bool(st.session_state.disable_safety_filters),
    help="Enable only for controlled testing scenarios.",
)
render_accessibility_controls()
apply_accessibility_styles()

if "messages" not in st.session_state:
    persisted_messages = load_session_messages(st.session_state.chat_session_id)
    st.session_state.messages = [
        AIMessage(content=message["content"]) if message["role"] == "assistant" else HumanMessage(content=message["content"])
        for message in persisted_messages
    ]

if not st.session_state.messages:
    greeting = AIMessage(content="Hello, I am a bot. How can I help you?")
    st.session_state.messages = [greeting]
    append_session_message(st.session_state.chat_session_id, "assistant", str(greeting.content))

session_counts = get_session_message_counts(st.session_state.chat_session_id)
st.sidebar.caption(
    "Session stats: "
    f"{session_counts['total']} total messages "
    f"({session_counts['user']} user / {session_counts['assistant']} assistant)"
)

st.sidebar.subheader("Export")
st.sidebar.download_button(
    "Download current chat (.md)",
    data=export_messages_as_markdown(
        st.session_state.messages,
        title=f"Conversation {st.session_state.chat_session_id}",
    ),
    file_name=f"{st.session_state.chat_session_id}.md",
    mime="text/markdown",
    use_container_width=True,
)
st.sidebar.download_button(
    "Download current chat (.json)",
    data=export_messages_as_json(st.session_state.messages),
    file_name=f"{st.session_state.chat_session_id}.json",
    mime="application/json",
    use_container_width=True,
)

for i, message in enumerate(st.session_state.messages):
    if isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.write(message.content)
            render_copy_button(str(message.content), key=f"assistant_msg_{i}")
    elif isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.write(message.content)

prompt = st.chat_input("Say something")

if prompt:
    if not isinstance(st.session_state.messages[-1], HumanMessage):
        st.session_state.messages.append(HumanMessage(content=prompt))  # type: ignore
        append_session_message(st.session_state.chat_session_id, "user", prompt)
        with st.chat_message("user"):
            st.write(prompt)

    if not isinstance(st.session_state.messages[-1], AIMessage):
        with st.chat_message("assistant"):
            try:
                response = st.write_stream(
                    stream_chat_response(
                        st.session_state.messages,
                        system_instruction=st.session_state.system_instruction,
                        max_history_messages=st.session_state.max_history_messages,
                        temperature=st.session_state.temperature,
                        disable_safety_filters=st.session_state.disable_safety_filters,
                    )
                )
            except Exception as err:
                st.error(f"Something went wrong talking to the model:\n\n`{err}`")
                st.info(
                    "If this was a temporary provider congestion issue, click "
                    "'Retry last response' in the sidebar."
                )
                if isinstance(st.session_state.messages[-1], HumanMessage):
                    st.session_state.messages.pop()
                    delete_last_message(st.session_state.chat_session_id, role="user")
            else:
                text = str(response) if response else "(No text returned from the model.)"
                st.session_state.messages.append(AIMessage(content=text))
                append_session_message(st.session_state.chat_session_id, "assistant", text)
                render_copy_button(text, key=f"assistant_msg_{len(st.session_state.messages) - 1}")

if st.session_state.get("retry_requested"):
    st.session_state.retry_requested = False
    if st.session_state.messages and isinstance(st.session_state.messages[-1], HumanMessage):
        with st.chat_message("assistant"):
            try:
                retry_response = st.write_stream(
                    stream_chat_response(
                        st.session_state.messages,
                        system_instruction=st.session_state.system_instruction,
                        max_history_messages=st.session_state.max_history_messages,
                        temperature=st.session_state.temperature,
                        disable_safety_filters=st.session_state.disable_safety_filters,
                    )
                )
            except Exception as err:
                st.error(f"Retry failed talking to the model:\n\n`{err}`")
                st.info("Try again in a few seconds, or switch to a lighter fallback model.")
            else:
                retry_text = str(retry_response) if retry_response else "(No text returned from the model.)"
                st.session_state.messages.append(AIMessage(content=retry_text))
                append_session_message(st.session_state.chat_session_id, "assistant", retry_text)
                render_copy_button(retry_text, key=f"assistant_msg_{len(st.session_state.messages) - 1}")
