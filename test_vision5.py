import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
from app.multimodal.image_service import analyze_image

try:
    res = analyze_image("what is the image?", "4/7290123bbcaf4aa6be5b7f1ad918ae2e.jpeg")
    print("FINAL RESULT:", repr(res))
except Exception as e:
    print("ERROR:", e)
