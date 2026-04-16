Use `streamlit run openrouter.py` to use with **Streamlit**

---

# Free LLM APIs Demo

[Ryan-PG](https://github.com/Ryan-PG/free-llm-model-apis-guide)

This repository demonstrates how to use **free or publicly accessible LLM APIs** with Python. It accompanies a YouTube video guide on using free LLM APIs effectively.

**Watch the video here:** [YouTube Video Link](LINK)
  - It includes two examples: 
    1. **GitHub/DeepSeek API** usage (`github.py`)
    2. **OpenRouter + Streamlit** for interactive prompts and image analysis (`openrouter.py`)

---

## Demo 1: GitHub / DeepSeek API

This script shows how to call an LLM hosted via GitHub or DeepSeek:
```bash
python github.py
```

It uses:
- `.env` file to store your API keys and endpoints
- `openai` Python client
- Example question: *“What is the capital of France?”*
You can switch models by updating the `model_name` variable.

---

## Demo 2: OpenRouter + Streamlit

This demo is an interactive web app using **Streamlit**:
```bash
streamlit run openrouter.py
```

Features:
- Input a text prompt or provide an image URL/upload an image.
- Get real-time AI responses directly in the browser.
- Choose between different free models:
  - `x-ai/grok-4-fast:free`
  - `x-ai/grok-4-vision:free`
  - `deepseek/DeepSeek-V3-0324:free`

---

## Setup

1. Clone the repo:
```bash
git clone <repo-url>
cd <repo-folder>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API credentials:
```env
GITHUB_API_KEY=your_github_api_key
GITHUB_MODELS_BASE_URL=your_github_endpoint
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_BASE_URL=your_openrouter_endpoint
```

4. Run either demo as described above.

---

## Resources & Guide
For a curated list of free LLM APIs and guidance, check out this gist:
[Free LLMs APIs Guide](https://ls.ryanheida.com/gist-free-llms-apis-guide)

## Notes
- This repo meant for **educational purposes** and to demonstrate practical usage of free LLM APIs.
- Make sure to handle API rate limits and credentials responsibly.

----

# Free LLM Models API Usage Guide: OpenRouter & GitHub

This guide explains how to use **free models** provided by [OpenRouter](https://openrouter.ai) and [GitHub Models](https://github.com/marketplace?type=models). 
It covers authentication, available free models, rate limits, and secure token management.

### Table of Contents:
1. OpenRouter Models
2. Github Models
3. Token Management with `.env`

---

# 🔹 OpenRouter Models

### How to Get a Token
1. Go to [OpenRouter Dashboard](https://openrouter.ai/keys).
2. Log in with your account.
3. Generate a new **API Key**.
4. Use this key in your requests:
  ```bash
  from openai import OpenAI
  
  client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="<OPENROUTER_API_KEY>",
  )
  
  completion = client.chat.completions.create(
    extra_body={},
    model="x-ai/grok-4-fast:free",
    messages=[
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "What is in this image?"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
            }
          }
        ]
      }
    ]
  )
  print(completion.choices[0].message.content)
  ```

### Free Models
You can explore free models here:
[Free-Models-on-OpenRouter](https://openrouter.ai/models?fmt=cards&max_price=0)
[Rate-Limits](https://openrouter.ai/docs/api-reference/limits#rate-limits-and-credits-remaining)

---

# 🔹 GitHub Models

### How to Get a Token
1. Go to [GitHub Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens).
2. Generate a new **Fine-grained PAT** with **`models:read`** scope enabled.
3. Use the token in your requests:
```bash
import os
from openai import OpenAI

token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.github.ai/inference"
model_name = "openai/gpt-4o-mini"

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
```

### Free Models
You can explore GitHub-hosted models here:
[GitHub-Marketplace-Models](https://github.com/marketplace?query=4o-mini&type=models)
Only models with **Low** or **High "Free rate limit tier"** can be used for free.
[Rate-Limits](https://openrouter.ai/docs/api-reference/limits#rate-limits-and-credits-remaining)

---

# 🔑 Token Management with `.env`

To keep your API tokens secure, save them inside a `.env` file instead of hardcoding them in code.

### Example `.env`
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
GITHUB_API_KEY=your_github_api_key_here
```

### Example Python Code
```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

openrouter_key = os.getenv("OPENROUTER_API_KEY")
github_key = os.getenv("GITHUB_API_KEY")

print("OpenRouter Key:", openrouter_key[:5] + "*****")  # mask output
print("GitHub Key:", github_key[:5] + "*****")
```

**Best Practices**
- **Don't** commit `.env` files to Git.
- Add `.env` to your `.gitignore`.
- Rotate your tokens if they are ever leaked.