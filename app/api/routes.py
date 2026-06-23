from fastapi import HTTPException

from app.auth.security import verify_password
from app.auth.jwt_handler import create_access_token

from app.memory.database import get_user_by_username
from fastapi import Depends
from app.auth.dependencies import get_current_user
from app.api.models import (
    LoginRequest,
    LoginResponse
)
from fastapi import APIRouter

from .models import (
    ChatRequest,
    ChatResponse,
    UploadResponse,
    DocumentInfo,
    DocumentsResponse,
    DeleteResponse,
    ConversationInfo,
    ConversationsResponse,
    NewConversationResponse,
    MessageInfo,
    MessagesResponse,
    UpdateTitleRequest,
)
from ..services.chat_service import generate_response
from ..rag.retriever import Retriever

from fastapi import UploadFile, File, HTTPException
import shutil
from pathlib import Path

from ..services.document_service import DocumentService
from ..memory.database import (
    list_conversations,
    create_conversation,
    update_conversation_title,
    get_messages,
    save_message,
    search_conversations,
    delete_conversation,
    get_stats,
    get_conversation_owner,
)
from app.auth.security import hash_password

from app.api.models import (
    RegisterRequest,
    RegisterResponse
)

from app.memory.database import (
    create_user,
    get_user_by_username
)
document_service = DocumentService()

router = APIRouter()

retriever = Retriever()


@router.get("/")
def home():
    return {
        "message": "Welcome to Athena AI API!"
    }


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user)
):

    result = generate_response(
        request.message,
        retriever,
        request.history,
        request.selected_documents,
    )
    print("Conversation ID =", request.conversation_id)
    if request.conversation_id:
        
        owner = get_conversation_owner(
            request.conversation_id
        )

        if not owner:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

        if owner[0] != current_user["user_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

        save_message(
            request.conversation_id,
            "user",
            request.message,
        )

        save_message(
            request.conversation_id,
            "assistant",
            result["answer"],
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


@router.get(
    "/conversations",
    response_model=ConversationsResponse,
)
def get_conversations(
    current_user=Depends(get_current_user)
):

    conversations = list_conversations(
        current_user["user_id"]
    )

    return ConversationsResponse(
        conversations=[
            ConversationInfo(
                id=row[0],
                title=row[1],
                created_at=row[2],
            )
            for row in conversations
        ]
    )

@router.post(
    "/conversations",
    response_model=NewConversationResponse,
)
def new_conversation(
    current_user=Depends(get_current_user)
):

    conversation_id = create_conversation(
        title="New Chat",
        user_id=current_user["user_id"]
    )
    return NewConversationResponse(
        id=conversation_id,
        title="New Chat",
    )
@router.get("/conversations/search")
def search_chat_history(
    query: str,
    current_user=Depends(get_current_user)
):

    conversations = search_conversations(
        query,
        current_user["user_id"]
    )

    return {
        "conversations": [
            {
                "id": row[0],
                "title": row[1],
                "created_at": row[2],
            }
            for row in conversations
        ]
    }

@router.delete(
    "/conversations/{conversation_id}"
)
def remove_conversation(
    conversation_id: int,
    current_user=Depends(get_current_user)
):

    delete_conversation(
        conversation_id,
        current_user["user_id"]
    )

    return {
        "success": True
    }
    
@router.get(
    "/conversations/{conversation_id}",
    response_model=MessagesResponse,
)
def get_conversation_messages(
    conversation_id: int,
    current_user=Depends(get_current_user)
):
    owner = get_conversation_owner(
        conversation_id
    )

    if not owner:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    if owner[0] != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )    

    messages = get_messages(
        conversation_id
    )

    return MessagesResponse(
        messages=[
            MessageInfo(
                role=row[0],
                content=row[1],
            )
            for row in messages
        ]
    )
@router.put(
    "/conversations/{conversation_id}/title"
)
def update_title(
    conversation_id: int,
    request: UpdateTitleRequest,
    current_user=Depends(get_current_user)
):

    owner = get_conversation_owner(
        conversation_id
    )

    if not owner:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    if owner[0] != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    update_conversation_title(
        conversation_id,
        request.title,
    )

    return {
        "success": True
    }
@router.get("/stats")
def stats():

    db_stats = get_stats()

    return {
        "documents":
            document_service.document_count(),

        "conversations":
            db_stats["conversations"],

        "messages":
            db_stats["messages"],
    }
@router.post(
    "/register",
    response_model=RegisterResponse
)
def register_user(request: RegisterRequest):

    existing_user = get_user_by_username(
        request.username
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    password_hash = hash_password(
        request.password
    )

    create_user(
        request.username,
        request.email,
        password_hash
    )

    return RegisterResponse(
        message="User created successfully"
    )
@router.post(
    "/login",
    response_model=LoginResponse
)
def login(request: LoginRequest):

    user = get_user_by_username(
        request.username
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    stored_hash = user[3]

    print("USERNAME =", request.username)
    print("PASSWORD =", request.password)
    print("HASH =", stored_hash)

    result = verify_password(
        request.password,
        stored_hash
    )

    print("VERIFY RESULT =", result)

    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token(
        {
            "user_id": user[0],
            "username": user[1]
        }
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer"
    )
