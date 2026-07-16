from app.memory.database import list_conversations
import time

print("Calling list_conversations...")
start = time.time()
try:
    rows = list_conversations(1)
    print("Done in", time.time() - start)
    print("Rows:", rows)
except Exception as e:
    print("Error:", e)
