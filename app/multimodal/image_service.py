from collections import Counter
from pathlib import Path
from .validators import validate_image
from ..providers.ollama_provider import ask_vision_llm
from PIL import Image
import time


def detect_dominant_color(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    with Image.open(path) as img:
        img = img.convert("RGB")
        img = img.resize((100, 100))
        pixels = list(img.getdata())

    counts = Counter(pixels)
    dominant_rgb, _ = counts.most_common(1)[0]

    named_colors = {
        "red": (255, 0, 0),
        "blue": (0, 0, 255),
        "green": (0, 128, 0),
        "yellow": (255, 255, 0),
        "orange": (255, 165, 0),
        "purple": (128, 0, 128),
        "pink": (255, 192, 203),
        "brown": (150, 75, 0),
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "grey": (128, 128, 128),
        "gray": (128, 128, 128),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255),
    }

    def distance(rgb1, rgb2):
        return sum((a - b) ** 2 for a, b in zip(rgb1, rgb2))

    best_match = min(named_colors, key=lambda name: distance(dominant_rgb, named_colors[name]))
    return best_match


def _extract_color_from_text(text: str) -> str | None:
    normalized = text.strip().lower()
    valid_colors = {
        "red", "blue", "green", "yellow", "orange", "purple", "pink",
        "brown", "black", "white", "grey", "gray", "cyan", "magenta",
    }

    if normalized in valid_colors:
        return normalized

    for color in valid_colors:
        if color in normalized:
            return color

    return None


def _format_color_sentence(color: str) -> str:
    return f"The colour of the image is {color}."


def analyze_image(prompt: str, image_path: str = None):
    print("===== IMAGE SERVICE =====")
    print("Image:", image_path)

    validate_image(image_path)
    print("Image validation passed")

    # Short and effective prompt
    full_prompt = f"""
Question: {prompt}

Answer the question in one complete short sentence, based on the image.
If the question is about colour, respond like: "The colour of the image is red."
"""

    print("Calling ask_vision_llm()")

    start = time.time()
    print("=" * 70)
    print("VISION PROMPT")
    print(full_prompt)
    print("=" * 70)
    result = ask_vision_llm(
        prompt=full_prompt,
        image_path=image_path,
    )

    normalized = result.strip()
    extracted_color = _extract_color_from_text(normalized)

    if extracted_color:
        normalized = _format_color_sentence(extracted_color)
    elif "colour" in prompt.lower() or "color" in prompt.lower():
        print("Vision model returned an invalid colour answer, falling back to dominant image color.")
        fallback_color = detect_dominant_color(image_path)
        normalized = _format_color_sentence(fallback_color)
    elif normalized and normalized.endswith("."):
        # Keep a well-formed sentence if the model returned one.
        pass
    elif normalized:
        # At least preserve non-empty model output if it is not a colour question.
        normalized = normalized
    else:
        normalized = ""

    print("\n" + "=" * 70)
    print("IMAGE SERVICE RESULT")
    print(type(normalized))
    print(repr(normalized))
    print("=" * 70)
    print(f"Vision took: {time.time() - start:.2f} seconds")
    print("ask_vision_llm() returned")
    return normalized


