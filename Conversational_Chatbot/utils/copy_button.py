"""Streamlit helper: copy arbitrary text to the clipboard from a button click."""

from __future__ import annotations

import json

import streamlit as st


def render_copy_button(text: str, *, key: str) -> None:
    """
    Render a 'Copy' button that copies `text` in the browser.

    Uses JSON to safely embed the string in JavaScript. `key` should be unique
    per button (e.g. message index).
    """
    safe_key = "".join(c if c.isalnum() else "_" for c in key)[:96]
    js_literal = json.dumps(text)
    st.iframe(
        f"""
        <div style="font-family: system-ui, sans-serif; margin-top: 0.35rem;">
            <button
                type="button"
                id="btn_{safe_key}"
                aria-label="Copy assistant reply to clipboard"
                title="Copy assistant reply to clipboard"
                style="padding: 0.45rem 0.95rem; min-height: 36px; cursor: pointer;
                       border-radius: 8px; border: 1px solid rgba(49, 51, 63, 0.35);
                       background: rgba(250, 250, 250, 1); font-size: 14px; line-height: 1.2;"
            >Copy reply</button>
            <span
                id="ok_{safe_key}"
                role="status"
                aria-live="polite"
                style="margin-left: 10px; font-size: 13px; color: #0d8050; display: none;"
            >Copied!</span>
        </div>
        <script>
            (function() {{
                const payload = {js_literal};
                const btn = document.getElementById("btn_{safe_key}");
                const ok = document.getElementById("ok_{safe_key}");
                if (!btn) return;
                btn.addEventListener("focus", function() {{
                    btn.style.outline = "2px solid #005fcc";
                    btn.style.outlineOffset = "2px";
                }});
                btn.addEventListener("blur", function() {{
                    btn.style.outline = "none";
                }});
                btn.addEventListener("click", async function() {{
                    try {{
                        if (!navigator.clipboard || !navigator.clipboard.writeText) {{
                            throw new Error("Clipboard API unavailable");
                        }}
                        await navigator.clipboard.writeText(payload);
                        ok.textContent = "Copied!";
                        ok.style.color = "#0d8050";
                        ok.style.display = "inline";
                        setTimeout(function() {{ ok.style.display = "none"; }}, 2000);
                    }} catch (e) {{
                        ok.textContent = "Clipboard blocked; use manual copy.";
                        ok.style.color = "#a04400";
                        ok.style.display = "inline";
                        window.prompt("Copy failed in this browser. Select the text below and press Ctrl+C:", payload);
                    }}
                }});
            }})();
        </script>
        """,
        height=58,
        width="content",
    )
