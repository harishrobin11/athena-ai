import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.append(str(Path.cwd()))

from app.services.chat_service import generate_response_stream
from app.rag.retriever import Retriever

async def main():
    print("Testing generate_response_stream...")
    async for chunk in generate_response_stream(
        user="What is the finance strategy?",
        retriever=Retriever(),
        conversation_id="test_conversation",
        history=[],
        selected_documents=[],
        user_id=1,
    ):
        print(f"CHUNK: {chunk.strip()}")

if __name__ == "__main__":
    asyncio.run(main())
