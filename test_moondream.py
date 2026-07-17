from ollama import chat

response = chat(
    model="moondream:latest",
    messages=[
        {
            "role": "user",
            "content": "What is the colour of this image?",
            "images": [
                "storage/uploads/106/bce55e39dea04199839220f475bf3c82.jpeg"
            ],
        }
    ],
    stream=True,
)

text = ""

for chunk in response:
    print(chunk)
    msg = chunk.get("message")
    if msg and msg.get("content"):
        text += msg["content"]

print("FINAL:", repr(text))