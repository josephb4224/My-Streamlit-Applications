"""Streamlit UI accessibility controls and styling helpers."""

from __future__ import annotations

import streamlit as st

_DEFAULTS: dict[str, float | bool] = {
    "ui_font_scale": 1.0,
    "ui_line_height": 1.55,
    "ui_high_contrast": False,
    "ui_reduce_motion": False,
}


def initialize_accessibility_state() -> None:
    """Initialize accessibility-related session state defaults."""
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_accessibility_controls() -> None:
    """Render sidebar controls for UI accessibility preferences."""
    st.sidebar.subheader("Accessibility")
    font_scale = float(st.session_state.get("ui_font_scale", _DEFAULTS["ui_font_scale"]))
    line_height = float(st.session_state.get("ui_line_height", _DEFAULTS["ui_line_height"]))
    st.session_state.ui_font_scale = st.sidebar.slider(
        "Text size",
        min_value=0.9,
        max_value=1.35,
        value=min(max(font_scale, 0.9), 1.35),
        step=0.05,
        help="Increase text size for chat messages and input area.",
    )
    st.session_state.ui_line_height = st.sidebar.slider(
        "Line spacing",
        min_value=1.3,
        max_value=1.9,
        value=min(max(line_height, 1.3), 1.9),
        step=0.05,
        help="Higher spacing can improve readability for longer responses.",
    )
    st.session_state.ui_high_contrast = st.sidebar.checkbox(
        "High-contrast message outlines",
        value=bool(st.session_state.get("ui_high_contrast", _DEFAULTS["ui_high_contrast"])),
        help="Emphasizes chat bubble boundaries and control outlines.",
    )
    st.session_state.ui_reduce_motion = st.sidebar.checkbox(
        "Reduce motion",
        value=bool(st.session_state.get("ui_reduce_motion", _DEFAULTS["ui_reduce_motion"])),
        help="Disables most transition and animation effects.",
    )

    if st.sidebar.button("Reset accessibility settings", use_container_width=True):
        for key, value in _DEFAULTS.items():
            st.session_state[key] = value
        st.rerun()


def apply_accessibility_styles() -> None:
    """Apply CSS tweaks based on current accessibility preferences."""
    font_scale = float(st.session_state.get("ui_font_scale", _DEFAULTS["ui_font_scale"]))
    line_height = float(st.session_state.get("ui_line_height", _DEFAULTS["ui_line_height"]))
    high_contrast = bool(st.session_state.get("ui_high_contrast", _DEFAULTS["ui_high_contrast"]))
    reduce_motion = bool(st.session_state.get("ui_reduce_motion", _DEFAULTS["ui_reduce_motion"]))

    contrast_styles = (
        """
        .stApp [data-testid="stChatMessage"] {
            border: 2px solid rgba(0, 0, 0, 0.7);
            border-radius: 0.85rem;
            padding: 0.25rem 0.4rem;
        }
        .stApp [data-testid="stSidebar"] button,
        .stApp [data-testid="stSidebar"] [role="button"] {
            border-width: 2px !important;
        }
        """
        if high_contrast
        else ""
    )

    motion_styles = (
        """
        .stApp *, .stApp *::before, .stApp *::after {
            animation: none !important;
            transition: none !important;
            scroll-behavior: auto !important;
        }
        """
        if reduce_motion
        else ""
    )

    st.markdown(
        f"""
        <style>
            .stApp [data-testid="stChatMessage"] p,
            .stApp [data-testid="stChatMessage"] li,
            .stApp [data-testid="stChatMessage"] code,
            .stApp [data-testid="stChatMessage"] pre {{
                font-size: {font_scale:.2f}rem !important;
                line-height: {line_height:.2f} !important;
            }}
            .stApp [data-testid="stChatInput"] textarea {{
                font-size: {font_scale:.2f}rem !important;
                line-height: {line_height:.2f} !important;
            }}
            .stApp [data-testid="stChatMessage"] pre {{
                white-space: pre-wrap;
                word-break: break-word;
            }}
            .stApp button:focus-visible,
            .stApp [role="button"]:focus-visible,
            .stApp input:focus-visible,
            .stApp select:focus-visible,
            .stApp textarea:focus-visible {{
                outline: 3px solid #005fcc !important;
                outline-offset: 2px !important;
            }}
            {contrast_styles}
            {motion_styles}
        </style>
        """,
        unsafe_allow_html=True,
    )

