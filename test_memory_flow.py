import time
from app.memory.extractor import extract_memories
from app.memory.store import save_memories, memory_collection
from app.tools.search_memory import search_memory

user_id = 3

print("1. Extracting memory...")
memories = extract_memories("My name is Harish")
print("Extracted:", memories)

print("2. Saving memory...")
save_memories(user_id=user_id, memories=memories)

print("3. Searching memory...")
result = search_memory("What is my name?", context={"user_id": user_id})
print("Search Result:", result)

print("4. All docs in chroma for user 3:")
all_docs = memory_collection.get(where={"user_id": user_id})
print(all_docs)
