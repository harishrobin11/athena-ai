import time
from app.agents.agent_executor import gather_global_context
from app.providers.ollama_provider import stream_llm

start = time.time()
ctx = gather_global_context(1, "hello")
print("gather_global_context took:", time.time() - start)

start = time.time()
print("Starting stream...")
for chunk in stream_llm([{"role": "user", "content": "hi"}]):
    pass
print("LLM took:", time.time() - start)
