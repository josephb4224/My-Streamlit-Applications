import os
import base64
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

st.title("Free Model Usage")
st.write("Enter your prompt and get the response.")

prompt = st.text_input("Prompt:", placeholder="What can you see in this image?")
img_url = st.text_input("Image URL:", placeholder="https://....")
uploaded_file = st.file_uploader("Or upload an image", type=["jpg", "jpeg", "png", "webp"])

slected_model = st.selectbox(
    "Select Model:",
    (
        "x-ai/grok-4-fast:free",
        "deepseek/DeepSeek-V3-0324:free",
    ),
)

def model_input(prompt, img_url, uploaded_file):
    if uploaded_file is not None:
        # Convert file to base64
        bytes_data = uploaded_file.read()
        b64_image = base64.b64encode(bytes_data).decode("utf-8")
        return [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                    },
                ],
            }
        ]

    if img_url.strip():
        return [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": img_url}},
                ],
            }
        ]

    return [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt}],
        }
    ]

if st.button("GO"):
    with st.spinner("Analyzing..."):
        completion = client.chat.completions.create(
            model=slected_model,
            messages=model_input(prompt, img_url, uploaded_file),  # type: ignore
        )
        st.subheader("AI Response")
        st.markdown(completion.choices[0].message.content)
