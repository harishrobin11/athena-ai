import asyncio
from app.services.chat_service import generate_response_stream
from app.rag.retriever import Retriever

async def test_stream():
    retriever = Retriever()
    stream = generate_response_stream(
        user="My name is Harish",
        retriever=retriever,
        conversation_id="test_conv",
        history=[],
        selected_documents=[],
        user_id=3,
        image_path=None
    )
    
    print("Consuming stream...")
    async for chunk in stream:
        if "__END__" in chunk:
            print("END SIGNAL RECEIVED")
        elif chunk.startswith("__GENERATION_ID__"):
            pass
        else:
            print(chunk, end="")
    print("\nStream consumed.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_stream())
