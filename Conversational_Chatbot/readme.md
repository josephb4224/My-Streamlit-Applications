# Conversational Chatbot (LangChain + Gemini + Streamlit)

Original inspiration: [np-n blog / conversational_chatbot_using_langchain_ang_gemini](https://github.com/np-n/blog_code_snippets/tree/master/conversational_chatbot_using_langchain_ang_gemini)

This project includes:
- Streamlit chat UIs (streaming and non-streaming)
- LangChain + Gemini integration with model failover
- SQLite conversation persistence
- Per-message copy buttons
- Runtime generation controls (temperature, context window, system instruction)
- Prompt behavior presets (concise, tutor, analyst, etc.)
- Accessibility controls (text size, line spacing, high-contrast outlines, reduced motion)
- Chat export to Markdown and JSON

---

## Requirements

```bash
pip install -r requirements.txt
```

`requirements.txt` includes:
- `langchain` (1.x)
- `langchain-core`
- `langchain-google-genai`
- `python-dotenv`
- `streamlit`

---

## Configuration

1. Copy `.env.example` to `.env`.
2. Add your Gemini key:

```env
GOOGLE_API_KEY=your_key_here
```

Optional settings:

```env
# Primary model
GEMINI_MODEL=gemini-2.5-flash

# Fallback models (comma-separated)
GEMINI_FALLBACK_MODELS=gemini-2.0-flash,gemini-1.5-flash

# Default generation temperature
GEMINI_TEMPERATURE=0.2

# Disable dangerous-content safety filtering (use only for controlled testing)
GEMINI_DISABLE_SAFETY_FILTERS=false
```

---

## Run

Streaming UI (recommended):

```bash
streamlit run streaming_app.py
```

Non-streaming UI:

```bash
streamlit run app.py
```

If browser auto-open fails, use [http://localhost:8501](http://localhost:8501).

---

## UI Features

- `Chat Controls`: switch sessions, start new chat, clear chat, retry last response.
- `Generation`: apply a prompt preset, then tune temperature, context window size, and live system instruction.
- `Accessibility`: tune text size/spacing, high-contrast outlines, and reduced motion.
- `Export`: download current conversation as `.md` or `.json`.
- Assistant bubble action: `Copy reply`.

---

## Project Layout

| Path | Purpose |
|------|---------|
| `streaming_app.py` | Streamlit app with token streaming |
| `app.py` | Streamlit app with full-turn replies |
| `utils/load_llm.py` | Gemini client setup and config |
| `utils/streaming_chain.py` | Streaming chain logic |
| `utils/chain.py` | Non-streaming chain logic |
| `utils/history.py` | Transcript formatting and context trimming |
| `utils/chat_store.py` | SQLite persistence helpers |
| `utils/export.py` | Markdown/JSON export helpers |
| `utils/presets.py` | Reusable system-instruction presets |
| `utils/ui_accessibility.py` | Sidebar accessibility controls and CSS |
| `utils/copy_button.py` | Clipboard copy button helper |
