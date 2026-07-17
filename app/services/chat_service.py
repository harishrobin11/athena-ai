
from ..rag.retriever import Retriever
from ..rag.prompt_builder import PromptBuilder
from ..core.prompts import SYSTEM_PROMPT
import uuid
from ..utils.image_storage import ImageStorage
from app.memory.extractor import extract_memories
from app.memory.store import save_memories
from ..providers.ollama_provider import (
    ask_llm,
    stream_llm,
)
from app.core.cancellation import (
    create_generation,
    is_cancelled,
    cleanup_generation,
)
from ..agents.agent_executor import (
    run_agent,
    run_agent_stream,
)
from ..memory.database import (
    init_db,
    create_conversation,
    save_message,
    load_history,
)

def generate_response(
    user,
    retriever,
    conversation_id=None,
    history=None,
    selected_documents=None,
    user_id=None,
    image_path=None,
):
    
    print("======== HISTORY ========")
    # Reuse the latest uploaded image if no new image is supplied
    if image_path is None and conversation_id:
        image_path = ImageStorage.latest_image(conversation_id)    

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

    answer = run_agent(
        user_query=user,
        user_id=user_id,
        selected_documents=selected_documents,
        image_path=image_path,
    )
    try:
        memories = extract_memories(user)

        if memories:
            save_memories(
                user_id=user_id,
                memories=memories,
            )

            print("Saved semantic memories:", memories)

    except Exception as e:
        print("Memory extraction failed:", e)    

    return {
        "answer": answer,
        "sources": [],
    }
    
def generate_response_stream(
    user: str,
    retriever: Retriever,
    conversation_id,
    history=None,
    selected_documents=None,
    user_id=None,
    image_path=None,
):
    # Reuse the latest uploaded image if this is a follow-up question
    if image_path is None and conversation_id:
        image_path = ImageStorage.latest_image(conversation_id)    
    if conversation_id:
        save_message(
            conversation_id,
            "user",
            user,
        )
    stream = run_agent_stream(
        user_query=user,
        user_id=user_id,
        selected_documents=selected_documents,
        image_path=image_path,
    )

    generation_id = str(uuid.uuid4())

    print(
        "BACKEND CREATED GENERATION ID =",
        generation_id
    )

    create_generation(generation_id)

    yield f"__GENERATION_ID__:{generation_id}\n"

    try:

        full_answer = ""

        for chunk in stream:
            print("YIELDING:", repr(chunk))

            if is_cancelled(generation_id):

                print(f"Generation cancelled: {generation_id}")

                yield "\n\n[Generation Cancelled]"

                break

            full_answer += chunk

            yield chunk

    finally:
        if conversation_id:
            save_message(
                conversation_id,
                "assistant",
                full_answer,
            )

        # -----------------------------
        # Extract & save semantic memories
        # -----------------------------
        try:
            memories = extract_memories(user)

            if memories:
                save_memories(
                    user_id=user_id,
                    memories=memories,
                )

                print("Saved semantic memories:", memories)

        except Exception as e:
            print("Memory extraction failed:", e)

        yield "__END__"

        cleanup_generation(generation_id)
        
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
            user=user,
            retriever=retriever,
            conversation_id=conversation_id,
            history=history,
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