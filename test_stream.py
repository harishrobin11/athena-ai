from app.providers.ollama_provider import stream_llm

messages = [
    {
        "role": "user",
        "content": "Tell me a short story."
    }
]

for chunk in stream_llm(messages):
    print(chunk, end="", flush=True)

print()