import base64
import requests

IMAGE = "storage/uploads/91/e7942197896e48a494c49900103f9122.jpeg"

with open(IMAGE, "rb") as f:
    img = base64.b64encode(f.read()).decode()

payload = {
    "model": "moondream:latest",
    "messages": [
        {
            "role": "user",
            "content": "What colour is this image?",
            "images": [img],
        }
    ],
    "stream": False,
}

print("Sending request...")

r = requests.post(
    "http://127.0.0.1:11434/api/chat",
    json=payload,
    timeout=300,
)

print("Status:", r.status_code)
print(r.text)