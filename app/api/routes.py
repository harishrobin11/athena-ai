from fastapi import APIRouter

from .models import (
    ChatRequest,
    ChatResponse,
    UploadResponse,
    DocumentInfo,
    DocumentsResponse,
    DeleteResponse,
)
from ..services.chat_service import generate_response
from ..rag.retriever import Retriever

from fastapi import UploadFile, File, HTTPException
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

    history = [
        (
            msg["role"],
            msg["content"],
        )
        for msg in request.history
    ]

    result = generate_response(
        request.message,
        retriever,
        history,
    )

    return ChatResponse(
        response=result["answer"],
        sources=result["sources"],
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
@router.get(
    "/documents",
    response_model=DocumentsResponse,
)
def list_documents():

    files = document_service.list_documents()

    return DocumentsResponse(
        documents=[
            DocumentInfo(
                filename=file,
            )
            for file in files
        ]
    )
@router.delete(
    "/documents/{filename}",
    response_model=DeleteResponse,
)
def delete_document(filename: str):

    deleted = document_service.delete_document(
        filename
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return DeleteResponse(
        success=True,
        filename=filename,
    )
