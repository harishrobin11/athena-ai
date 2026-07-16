import json

from app.providers.ollama_provider import ask_llm
from app.core.memory_prompt import MEMORY_EXTRACTION_PROMPT


def extract_memories(message: str):
    """
    Extract long-term semantic memories from a user message.

    Returns:
        List[dict]
    """

    prompt = f"""
{MEMORY_EXTRACTION_PROMPT}

User Message:
{message}
"""

    response = ask_llm(
        [
            {
                "role": "user",
                "content": prompt,
            }
        ]
    )

    print("===== MEMORY EXTRACTION =====")
    print(response)

    try:
        # Clean markdown code blocks from the response
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
            
        memories = json.loads(cleaned_response.strip())

        # Normalize to list
        if isinstance(memories, dict):
            memories = [memories]

        if not isinstance(memories, list):
            return []

        return memories

    except Exception as e:
        print("Memory parse error:", e)
        return []