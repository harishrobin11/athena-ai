from app.services.chat_service import generate_response_stream
from app.rag.retriever import Retriever

retriever = Retriever()

import asyncio

async def run_test():
    async for chunk in generate_response_stream(
        user="What is artificial intelligence?",
        retriever=retriever,
        conversation_id="test_conv",
        user_id=1,
    ):
        print(chunk, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(run_test())