
from ..rag.retriever import Retriever
from ..rag.prompt_builder import PromptBuilder
from ..core.prompts import SYSTEM_PROMPT
from ..providers.ollama_provider import ask_llm
from ..memory.database import (
    init_db,
    create_conversation,
    save_message,
    load_history,
)

def generate_response(user: str, retriever: Retriever):
    
    documents = retriever.retrieve(user)

    prompt = PromptBuilder.build(
        user,
        documents,
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    answer = ask_llm(messages)

    sources = PromptBuilder.get_sources(documents)

    return {
        "answer": answer,
        "sources": sources,
    }
def chat():
    init_db()

    conversation_id = create_conversation()
    retriever = Retriever()

    print("Athena AI")
    print("Type 'exit' to quit.\n")

    while True:

        user = input("You: ")

        if user.lower() == "exit":
            print("Athena: Goodbye!")
            break

        save_message(conversation_id, "user", user)

        # history = load_history(conversation_id)

        # messages = [
        #     {
        #         "role": "system",
        #         "content": SYSTEM_PROMPT,
        #     }
        # ]

        # for role, content in history:
        #     messages.append(
        #         {
        #             "role": role,
        #             "content": content,
        #         }
        #     )

        result = generate_response(
            user,
            retriever,
        )

        answer = result["answer"]

        save_message(
            conversation_id,
            "assistant",
            answer,
        )

        print("\nAthena:")
        print(answer)
        print()