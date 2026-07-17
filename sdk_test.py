from ollama import chat

response = chat(
    model="moondream:latest",
    messages=[
        {
            "role": "user",
            "content": "Describe this image.",
            "images": [
                "storage/uploads/91/e7942197896e48a494c49900103f9122.jpeg"
            ],
        }
    ],
)

print(response)