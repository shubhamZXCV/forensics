import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OLLAMA_API_KEY")
API_URL = os.getenv("OLLAMA_API_URL")
MODEL = os.getenv("OLLAMA_MODEL")

print(f"Testing URL: {API_URL}")
print(f"Testing Model: {MODEL}")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

import base64

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

image_path = "test_video_frame_0_mask.png"
base64_image = encode_image(image_path)

data = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What do you see in this image? Is there a white mask?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    "stream": True
}

try:
    print(f"\n--- Testing Endpoint: {API_URL} ---")
    response = requests.post(API_URL, headers=headers, json=data, stream=True, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("Response Stream:")
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    line = line[6:]
                if line == "[DONE]":
                    break
                try:
                    json_data = json.loads(line)
                    delta = json_data.get("choices", [{}])[0].get("delta", {})
                    if "content" in delta:
                        print(delta["content"], end="", flush=True)
                except json.JSONDecodeError:
                    pass
        print("\n\n✅ Endpoint is working!")
        sys.exit(0)
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")

sys.exit(1)
