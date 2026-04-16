import streamlit as st

from utils.chain import run_chat_turn
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
from utils.streaming_chain import DEFAULT_SYSTEM_INSTRUCTION
from utils.ui_accessibility import (
    apply_accessibility_styles,
    initialize_accessibility_state,
    render_accessibility_controls,
)

st.set_page_config(page_title="Conversational Bot!")
st.title("Gemini Chatbot 💬")

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
    st.session_state.messages = load_session_messages(selected_session_id)
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
        and st.session_state.messages[-1]["role"] == "assistant"
        and st.session_state.messages[-2]["role"] == "user"
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
    st.session_state.messages = load_session_messages(st.session_state.chat_session_id)

if not st.session_state.messages:
    initial_message = {"role": "assistant", "content": "Hi, I am a bot. How can I help you?"}
    st.session_state.messages = [initial_message]
    append_session_message(
        st.session_state.chat_session_id,
        initial_message["role"],
        initial_message["content"],
    )

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
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant":
            render_copy_button(message["content"], key=f"assistant_msg_{i}")

prompt = st.chat_input("Say something")

if prompt:
    if st.session_state.messages[-1]["role"] != "user":
        st.session_state.messages.append({"role": "user", "content": prompt})
        append_session_message(st.session_state.chat_session_id, "user", prompt)
        with st.chat_message("user"):
            st.write(prompt)

    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            try:
                reply = run_chat_turn(
                    st.session_state.messages,
                    system_instruction=st.session_state.system_instruction,
                    max_history_messages=st.session_state.max_history_messages,
                    temperature=st.session_state.temperature,
                    disable_safety_filters=st.session_state.disable_safety_filters,
                )
            except Exception as err:
                st.error(f"Something went wrong talking to the model:\n\n`{err}`")
                if st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()
                    delete_last_message(st.session_state.chat_session_id, role="user")
            else:
                st.session_state.messages.append({"role": "assistant", "content": reply})
                append_session_message(st.session_state.chat_session_id, "assistant", reply)
                st.write(reply)
                render_copy_button(
                    reply,
                    key=f"assistant_msg_{len(st.session_state.messages) - 1}",
                )

if st.session_state.get("retry_requested"):
    st.session_state.retry_requested = False
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            try:
                retry_reply = run_chat_turn(
                    st.session_state.messages,
                    system_instruction=st.session_state.system_instruction,
                    max_history_messages=st.session_state.max_history_messages,
                    temperature=st.session_state.temperature,
                    disable_safety_filters=st.session_state.disable_safety_filters,
                )
            except Exception as err:
                st.error(f"Retry failed talking to the model:\n\n`{err}`")
            else:
                st.session_state.messages.append({"role": "assistant", "content": retry_reply})
                append_session_message(st.session_state.chat_session_id, "assistant", retry_reply)
                st.write(retry_reply)
                render_copy_button(
                    retry_reply,
                    key=f"assistant_msg_{len(st.session_state.messages) - 1}",
                )
