from ollama import chat

response = chat(
    model="moondream:latest",
    messages=[
        {
            "role": "user",
            "content": "Describe this image.",
            "images": [
                "app/ui/assets/brain.png"
            ],
        }
    ],
)

print(response)