import requests

url = "http://127.0.0.1:8000/chat/image/stream"

with open("app/ui/assets/brain.png", "rb") as f:
    files = {"image": ("test.jpg", f, "image/jpeg")}
    data = {
        "message": "what is the image?",
        "conversation_id": "test_conv_id"
    }
    headers = {"Authorization": "Bearer test"} # Wait, I don't have a token.
