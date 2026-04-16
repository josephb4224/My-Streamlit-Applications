import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

token = os.getenv("GITHUB_API_KEY")
endpoint = os.getenv("GITHUB_MODELS_BASE_URL")
# model_name = "openai/gpt-4o-mini"
model_name = "deepseek/DeepSeek-V3-0324"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": "What is the capital of France?",
        }
    ],
    temperature=1.0,
    top_p=1.0,
    max_tokens=1000,
    model=model_name
)

print(response.choices[0].message.content)