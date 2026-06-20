from ollama import chat


def ask_llm(messages):
    response = chat(
        model="llama3.2:3b",
        messages=messages,
    )

    return response["message"]["content"]