from app.services.chat_service import generate_response_stream
from app.rag.retriever import Retriever

retriever = Retriever()

for chunk in generate_response_stream(
    user="What is artificial intelligence?",
    retriever=retriever,
    user_id=1,
):
    print(chunk, end="", flush=True)