
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

def generate_response(
    user: str,
    retriever: Retriever,
    history=None,
    selected_documents=None,
    user_id=None,
):
    print("======== HISTORY ========")

    if history:
        print(history)

        print("=========================")
    
    search_query = user

    if history:
        recent = history[-2:]
        context_text = " ".join(
            content
            for _, content in recent
        )

        search_query = (
            context_text + " " + user
        )
    print("STEP 1 - received query")
    filter_metadata = {
        "user_id": user_id
    }

    if selected_documents:
        
        if len(selected_documents) == 1:

            filter_metadata = {
                "$and": [
                    {"user_id": user_id},
                    {
                        "source":
                        f"documents/user_{user_id}/{selected_documents[0]}"
                    }
                ]
            }

    documents = retriever.retrieve(
        search_query,
        filter_metadata=filter_metadata,
    )
    print("STEP 2 - retrieval complete")

    prompt = PromptBuilder.build(
        user,
        documents,
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    if history:

        for role, content in history:

            messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )
    print("STEP 3 - calling LLM")
    answer = ask_llm(messages)
    print("STEP 4 - LLM complete")
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

        history = load_history(conversation_id)

        result = generate_response(
            user,
            retriever,
            history,
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