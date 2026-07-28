import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
from app.providers.ollama_provider import ask_vision_llm

full_prompt = """
Question: what is the image?

Answer the question in one complete short sentence, based on the image.
If the question is about colour, respond like: "The colour of the image is red."
"""

try:
    res = ask_vision_llm(full_prompt, "4/7290123bbcaf4aa6be5b7f1ad918ae2e.jpeg")
    print("RESULT:", repr(res))
except Exception as e:
    print("ERROR:", e)
