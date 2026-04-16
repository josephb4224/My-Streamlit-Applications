#!/usr/bin/env python3
# List all OpenRouter.AI Models & their Properties:
import requests

url = "https://openrouter.ai/api/v1/models"
headers = {"Authorization": "Bearer <token>"}
response = requests.get(url, headers=headers)
print(response.json())