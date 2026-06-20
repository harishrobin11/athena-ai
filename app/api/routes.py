from fastapi import APIRouter

from .models import (
    ChatRequest,
    ChatResponse,
    UploadResponse,
)
from ..services.chat_service import generate_response
from ..rag.retriever import Retriever

from fastapi import UploadFile, File
import shutil
from pathlib import Path

from ..services.document_service import DocumentService

document_service = DocumentService()

router = APIRouter()

retriever = Retriever()


@router.get("/")
def home():
    return {
        "message": "Welcome to Athena AI API!"
    }


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    answer = generate_response(
        request.message,
        retriever,
    )

    return ChatResponse(
        response=answer
    )
    
@router.post("/upload", response_model=UploadResponse)
def upload(file: UploadFile = File(...)):

    documents_dir = Path("documents")
    documents_dir.mkdir(exist_ok=True)

    destination = documents_dir / file.filename

    with open(destination, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    chunks = document_service.ingest(str(destination))

    return UploadResponse(
        filename=file.filename,
        chunks=chunks,
    )