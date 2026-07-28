import os

API_URL = os.getenv(
    "ATHENA_API_URL",
    "http://127.0.0.1:8000",
)

DOCUMENTS_API = f"{API_URL}/documents"

CONVERSATIONS_API = f"{API_URL}/conversations"

UPLOAD_API = f"{API_URL}/upload"

STREAM_API_URL = f"{API_URL}/chat/stream"

IMAGE_STREAM_API_URL = (
    f"{API_URL}/chat/image/stream"
)

STATS_API = f"{API_URL}/stats"

CANCEL_API_URL = f"{API_URL}/cancel"