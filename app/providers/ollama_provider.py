import base64
from pathlib import Path
import requests
from ollama import chat

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/v1/chat/completions"

TEXT_MODEL = "llama3.2:3b"
VISION_MODEL = "moondream:latest"


# --------------------------------------------------
# TEXT MODEL
# --------------------------------------------------

def ask_llm(messages):
    """
    Non-streaming text inference.
    """
    response = chat(
        model=TEXT_MODEL,
        messages=messages,
        keep_alive="30m",
    )

    return response["message"]["content"]


def stream_llm(messages):
    """
    Streaming text inference.
    """

    print("Starting Ollama stream...")

    stream = chat(
        model=TEXT_MODEL,
        messages=messages,
        stream=True,
        keep_alive="30m",
        options={
            "num_predict": 1024,
            "temperature": 0.7,
        },
    )

    for chunk in stream:

        content = chunk["message"]["content"]

        if content:
            yield content


# --------------------------------------------------
# VISION MODEL
# --------------------------------------------------



def _load_image_b64(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    with open(path, "rb") as f:
        image_bytes = f.read()

    return base64.b64encode(image_bytes).decode("utf-8")


def ask_vision_llm(
    prompt: str,
    image_path: str,
):
    print("===== VISION PROVIDER =====")

    image_b64 = _load_image_b64(image_path)

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [image_b64],
            }
        ],
        "stream": False,
        "max_tokens": 64,
        "temperature": 0.0,
    }

    print("Sending vision request to Ollama HTTP API")
    response = requests.post(
        OLLAMA_CHAT_URL,
        json=payload,
        timeout=300,
    )
    print("HTTP status:", response.status_code)
    print("RAW RESPONSE:", response.text[:2000])
    response.raise_for_status()

    data = response.json()
    content = ""
    if isinstance(data, dict):
        choices = data.get("choices") or []
        if choices:
            first = choices[0]
            message = first.get("message") or {}
            content = message.get("content") or ""

    print("VISION RESPONSE:", repr(content))
    return content.strip()

def stream_vision_llm(
    prompt: str,
    image_path: str,
):
    image_b64 = _load_image_b64(image_path)

    stream = chat(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [image_b64],
            }
        ],
        stream=True,
        keep_alive="30m",
    )

    for chunk in stream:
        message = chunk.get("message")
        if not message:
            continue

        content = message.get("content")
        if content:
            yield content