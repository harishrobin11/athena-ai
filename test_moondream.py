from ollama import chat

response = chat(
    model="moondream:latest",
    messages=[
        {
            "role": "user",
            "content": "What is the colour of this image?",
            "images": [
                "app/ui/assets/brain.png"
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