import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
from app.providers.ollama_provider import ask_vision_llm

full_prompt = "Please answer this based on the image in a short sentence: what is the image?"

try:
    res = ask_vision_llm(full_prompt, "4/7290123bbcaf4aa6be5b7f1ad918ae2e.jpeg")
    print("RESULT:", repr(res))
except Exception as e:
    print("ERROR:", e)
