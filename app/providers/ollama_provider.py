"""
Athena AI - Ollama Model Inference Provider Interface
Module: app.providers.ollama_provider
Description: Standardizes client connection frames for local text completions 
             and multi-modal structural vision loops utilizing the official client library.
"""

import base64
from pathlib import Path
from typing import List, Dict, Any, Generator
import ollama

TEXT_MODEL = "llama3.2:3b"
VISION_MODEL = "moondream:latest"


# =====================================================================
# STANDARD TEXT INFERENCE PIPELINES
# =====================================================================

def ask_llm(messages: List[Dict[str, Any]]) -> str:
    """
    Executes a blocking, non-streaming text completion routine.
    """
    try:
        response = ollama.chat(
            model=TEXT_MODEL,
            messages=messages,
            keep_alive="30m",
        )
        # Handle library object attribute extraction safely
        if hasattr(response, 'message'):
            return response.message.content
        return response.get('message', {}).get('content', '')
    except Exception as e:
        print(f"[OLLAMA ERROR] Synchronous inference failure: {e}")
        return f"Inference engine execution error: {str(e)}"


def stream_llm(messages: List[Dict[str, Any]]) -> Generator[str, None, None]:
    """
    Robust generative token generator tracking local model streams 
    with dot-attribute object syntax mappings.
    """
    print(f"Starting Ollama token stream using model target: {TEXT_MODEL}...")
    
    try:
        stream = ollama.chat(
            model=TEXT_MODEL,
            messages=messages,
            stream=True,
            keep_alive="30m",
            options={
                "num_predict": 512,
                "temperature": 0.7,
                "num_thread": 4,
                "num_ctx": 1024,
            },
        )

        
        for chunk in stream:
            # FIX: Safely parse chunk using modern library object attributes
            if hasattr(chunk, 'message') and chunk.message:
                content = chunk.message.content
                if content:
                    yield content
            elif isinstance(chunk, dict):
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
                    
    except Exception as e:
        print(f"[OLLAMA CRITICAL] Stream iteration pipeline collapsed: {e}")
        yield f"\n[Inference Stream Disconnected: {str(e)}]"


# =====================================================================
# MULTI-MODAL VISION INFERENCE PIPELINES
# =====================================================================

from app.services.storage_service import storage_service

def _load_image_b64(image_path: str) -> str:
    """Safely reads imagery from S3 into standard base64 strings."""
    # image_path is the object_key (e.g. 1/8f94c67106414680b68e912ac4dd0a6e.jpeg)
    file_bytes = storage_service.get_file_bytes("athena-images", image_path)
    return base64.b64encode(file_bytes).decode("utf-8")


def ask_vision_llm(prompt: str, image_path: str) -> str:
    """
    Evaluates imagery inputs synchronously utilizing native client definitions.
    """
    print("===== VISION PROVIDER SYNCHRONOUS INITIATION =====")
    try:
        image_b64 = _load_image_b64(image_path)
        
        response = ollama.chat(
            model=VISION_MODEL,
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [image_b64]
            }],
            keep_alive="30m",
        )
        
        if hasattr(response, 'message'):
            return response.message.content.strip()
        return response.get('message', {}).get('content', '').strip()
        
    except Exception as e:
        print(f"[OLLAMA VISION ERROR] Static canvas description pipeline failed: {e}")
        return f"Vision analytics engine failure: {str(e)}"


def stream_vision_llm(prompt: str, image_path: str) -> Generator[str, None, None]:
    """
    Streams multi-modal vision tokens dynamically for dashboard visualization pipelines.
    """
    print(f"Starting Ollama visual token stream using model target: {VISION_MODEL}...")
    try:
        image_b64 = _load_image_b64(image_path)
        
        stream = ollama.chat(
            model=VISION_MODEL,
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [image_b64]
            }],
            stream=True,
            keep_alive="30m",
        )
        
        for chunk in stream:
            if hasattr(chunk, 'message') and chunk.message:
                content = chunk.message.content
                if content:
                    yield content
            elif isinstance(chunk, dict):
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
                    
    except Exception as e:
        print(f"[OLLAMA VISION CRITICAL] Multi-modal text stream engine failure: {e}")
        yield f"\n[Vision Stream Disconnected: {str(e)}]"