"""
Athena AI - Core Routing Engine
Module: app.api.routes
Description: Unified REST API Gateway orchestrating core authentication, 
             conversational memory frameworks, RAG index operations, and 
             Sprint 20 layout-aware transaction automation with multi-tenant RBAC profiles.
"""

import os
import re
import uuid
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

import pdfplumber
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field

# Authentication & Security Infrastructure (Circular-Dependency Proof)
from app.auth.security import hash_password, verify_password
from app.auth.jwt_handler import create_access_token
from app.auth.dependencies import get_current_user, DepartmentGuard
from app.db.database import get_db
from app.api.models import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    DepartmentRole
)

# Core Chat & RAG Component Engines
from app.core.cancellation import cancel_generation
from app.utils.image_storage import ImageStorage
from app.services.chat_service import generate_response, generate_response_stream
from app.services.document_service import DocumentService
from app.services.storage_service import storage_service
from app.rag.retriever import Retriever
from app.providers.ollama_provider import ask_llm, stream_llm

# Downstream Database Connector Methods
from app.memory.database import (
    create_user,
    get_user_by_username,
    list_conversations,
    create_conversation,
    update_conversation_title,
    get_messages,
    save_message,
    search_conversations,
    delete_conversation,
    get_stats,
    get_conversation_owner,
    add_document,
    list_documents,
    delete_document_by_user,
    owns_document,
)

# Core Sprint 20 Machine Learning Tool Contract Imports
from app.tools.expense_tool import ExpenseClassificationTool
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

# 🦉 Master API Core Router Definition
router = APIRouter()

# Singleton Shared System Components Initialization
retriever = Retriever()
document_service = DocumentService()
expense_tool = ExpenseClassificationTool()

# =====================================================================
# REQUEST/RESPONSE SCHEMAS FOR FINANCIAL INTELLIGENCE ROUTING
# =====================================================================
class ExpensePredictionRequest(BaseModel):
    descriptions: List[str] = Field(..., example=["AWS Cloud Compute Invoice", "Uber to airport"])

class SinglePredictionResult(BaseModel):
    category: str
    confidence: float

class ExpensePredictionResponse(BaseModel):
    status: str
    predictions: List[SinglePredictionResult]

class EnrichedLedgerItem(BaseModel):
    raw_text: str
    predicted_category: str
    confidence_score: str

class StructuredDocumentPayload(BaseModel):
    total_lines_processed: int
    enriched_records: List[EnrichedLedgerItem]

# Global Server-Sent Events (SSE) Serializer Helper
def sse_data(chunk: str) -> str:
    if chunk in ("__END__", "__GENERATION_ID__"):
        return f"data: {chunk}\n\n"
    if chunk.startswith("__GENERATION_ID__:"):
        return f"data: {chunk}\n\n"
    return f"data: {json.dumps(chunk)}\n\n"


# =====================================================================
# SYSTEM USER MANAGEMENT & MULTI-TENANT SECURITY ENDPOINTS
# =====================================================================
@router.post("/register", response_model=RegisterResponse)
def register_user(request: RegisterRequest):
    existing_user = get_user_by_username(request.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    password_hash = hash_password(request.password)
    create_user(
        username=request.username, 
        email=request.email, 
        hashed_password=password_hash, 
        department=request.department.value
    )
    return RegisterResponse(message="User created successfully")

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    user = get_user_by_username(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    stored_hash = user[3]
    user_department = user[4] if len(user) > 4 else "PROCUREMENT"

    if not verify_password(request.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Temporary hardcode: grant 'admin' role if username is admin OR department is ADMIN
    granted_role = "admin" if user[1].lower() == "admin" or user_department == "ADMIN" else "analyst"
    
    token = create_access_token({
        "user_id": user[0], 
        "username": user[1], 
        "department": user_department
    })
    return LoginResponse(access_token=token, token_type="bearer", department=user_department, role=granted_role)


# =====================================================================
# ROLE-BASED ACCESS CONTROL (RBAC) ISOLATED WORKSPACES
# =====================================================================
@router.get("/analytics/financial-data")
def get_isolated_ledger_analytics(
    current_user: Any = Depends(DepartmentGuard([DepartmentRole.FINANCE]))
):
    """
    Blocks execution requests completely unless the authenticated user 
    is assigned to the target operational department block.
    """
    return {
        "message": "Tenant access verified successfully.",
        "active_tenant": current_user["username"],
        "scope": current_user.get("department", "PROCUREMENT")
    }


# =====================================================================
# SYSTEM CORE BASE & STATS DISCOVERY
# =====================================================================
@router.get("/")
def home():
    return {"message": "Welcome to Athena AI API!"}

@router.get("/stats")
def stats(workspace_id: Optional[int] = None, current_user=Depends(get_current_user), db=Depends(get_db)):
    if workspace_id:
        from app.auth.permissions import check_workspace_permission
        check_workspace_permission(workspace_id, ["owner", "admin", "manager"], current_user, db)
        
    db_stats = get_stats(workspace_id)
    return {
        "documents": db_stats["documents"],
        "conversations": db_stats["conversations"],
        "messages": db_stats["messages"],
    }

# =====================================================================
# INTENT ENGINE CHAT & REALTIME RETRIEVAL OPERATIONS
# =====================================================================

INSTANT_RESPONSE_PHRASES = {
    # --- 1. Standard Greetings & Openers ---
    "hello", "hi", "hey", "hello there", "hey there", "greetings", "yo", "hola",
    "good morning", "good afternoon", "good evening", "howdy", "hi ya", "hey computer",
    "is anyone there", "anybody home", "wake up", "are you awake",
    
    # --- 2. Conversational Small Talk & Wellness ---
    "how are you", "how are you doing", "how is it going", "how's it going", 
    "what's up", "what is up", "whats up", "how have you been", "how's life",
    "how was your day", "are you having a good day", "how do you feel",
    
    # --- 3. Gratitude, Agreement & Positive Feedback ---
    "thank you", "thanks", "thank you so much", "perfect", "awesome", "great", 
    "cool", "ok", "okay", "got it", "makes sense", "nice", "excellent", "superb",
    "sounds good", "no problem", "you rock", "brilliant", "understand", "i understand",
    
    # --- 4. Identity, Purpose & Capabilities ---
    "who are you", "what is your name", "whats your name", "who created you", 
    "what is athena", "what is athena ai", "what can you do", "help me", "help", 
    "how does this work", "what is this app", "what is this", "what are your features",
    "tell me what you do", "what is your purpose", "how do I use this",
    
    # --- 5. Navigation & UI Troubleshooting ---
    "how to upload files", "how to upload a file", "how do i upload", "how to upload",
    "how to switch workspaces", "where is the chat", "where is the database",
    "how to clear chat", "how to start a new chat", "where are my files",
    
    # --- 6. General Capabilities (To clarify you aren't just a basic search engine) ---
    "can you write code", "do you know python", "can you analyze data",
    "can you help me with ml", "what models do you use", "are you a language model",
    
    # --- 7. Farewells & Wrap-Ups ---
    "bye", "goodbye", "see you", "see you later", "talk to you later", "goodnight",
    "i am leaving", "gotta go", "catch you later", "have a good day", "have a nice day",

    # --- 8. Conversational Slang & Text Abbreviations ---
    "sup", "wru", "hru", "nm", "nvm", "brb", "btw", "idk", "idc", "tbh", "thx", 
    "ty", "tyvm", "np", "k", "kk", "gotcha", "bet", "word", "alright", "chill",

    # --- 9. Emotional Outbursts & Exclamations ---
    "oh", "oh wow", "oh really", "no way", "seriously", "damn", "damn it", "crap",
    "yikes", "oof", "phew", "yay", "hurray", "hooray", "uh oh", "uhoh", "yolo",

    # --- 10. Casual Open-Ended Prompts / Boredom ---
    "i'm bored", "im bored", "entertain me", "tell me something", "tell me a story",
    "tell me a secret", "surprise me", "what's new", "whats new", "give me a quote",

    # --- 11. User Status Updates (Stating user actions) ---
    "i am back", "im back", "i am here", "im here", "ready", "i am ready", "im ready",
    "let's go", "lets go", "let's do it", "lets do it", "hit me", "shoot", "fire away",
    "i'm listening", "im listening", "go ahead",

    # --- 12. Real-Time Thinking / Text Stuttering Fillers ---
    "um", "uh", "hmm", "hmmm", "well", "so", "like", "er", "ah", "basically", 
    "anyway", "anyways", "moving on", "let me see", "let me think",

    # --- 13. Feedback, Praise & Validation ---
    "you are good", "youre good", "nice job", "good job", "well done", "perfecto",
    "you are smart", "youre smart", "genius", "lifesaver", "you are amazing",
    "clutch", "goated", "sweet", "dope", "epic", "legend",

    # --- 14. Deep Disagreement or Corrections ---
    "wrong", "that's wrong", "thats wrong", "incorrect", "not true", "stop lying",
    "you are wrong", "youre wrong", "that is incorrect", "nope", "not at all",

    # --- 15. AI Limits & Meta Queries ---
    "are you a robot", "are you human", "do you think", "are you alive", 
    "do you have feelings", "are you real", "what model are you", "who is your boss"
}

TRIVIA_KEYWORDS = {
    "capital of", "who wrote", "who painted", "largest country", "smallest country",
    "speed of light", "distance to", "how many elements", "periodic table",
    "who discovered", "meaning of life", "tallest mountain", "deepest ocean",
    "who was the first", "invented the", "formula for", "population of"
}

TRIVIA_STARTERS = (
    "what is the capital", "who is the prime minister", "who is the president",
    "tell me a fact", "give me a random fact", "what is the meaning of",
    "how many states in", "what is the square root of"
)

def is_general_knowledge_or_trivia(message: str) -> bool:
    cleaned = message.strip().lower()
    
    if cleaned in INSTANT_RESPONSE_PHRASES:
        return True
    if any(keyword in cleaned for keyword in TRIVIA_KEYWORDS):
        return True
    if cleaned.startswith(TRIVIA_STARTERS):
        return True
        
    return False

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]
    user_message = request.message.strip().lower()

    active_username = current_user.get("full_name") or current_user.get("username", "User")
    from app.core.prompts import SYSTEM_PROMPT_TEMPLATE
    dynamic_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(username=active_username)

    if is_general_knowledge_or_trivia(user_message):
        # ⚡️ FAST PATH: Pass the message + dynamic prompt directly to the LLM
        try:
            db_history = request.history or []

            messages = [{"role": "system", "content": dynamic_system_prompt}]
            messages.extend(db_history)
            messages.append({"role": "user", "content": request.message})

            answer = ask_llm(messages)
            
            if request.conversation_id:
                save_message(request.conversation_id, "user", request.message)
                save_message(request.conversation_id, "assistant", answer)

            return ChatResponse(response=answer, sources=[])
        except Exception as e:
            return ChatResponse(response=f"Error connecting to LLM: {str(e)}", sources=[])
    
    if request.conversation_id:
        owner = get_conversation_owner(request.conversation_id)
        if not owner:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        if owner[0] != user_id:
            raise HTTPException(status_code=403, detail="Access denied to memory framework")
            
        save_message(request.conversation_id, "user", request.message)

    db_history = []
    if request.conversation_id:
        raw_msgs = get_messages(request.conversation_id)
        db_history = [{"role": row[0], "content": row[1]} for row in raw_msgs]
    else:
        db_history = request.history or []

    result = generate_response(
        user=request.message,
        retriever=retriever,
        history=db_history,
        selected_documents=request.selected_documents,
        user_id=user_id,
    )
    
    if request.conversation_id:
        save_message(request.conversation_id, "assistant", result["answer"])
        
    return ChatResponse(response=result["answer"], sources=result["sources"])

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, current_user=Depends(get_current_user)):
    user_message = request.message.strip().lower()
    
    active_username = current_user.get("full_name") or current_user.get("username", "User")
    from app.core.prompts import SYSTEM_PROMPT_TEMPLATE
    dynamic_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(username=active_username)

    if is_general_knowledge_or_trivia(user_message):
        # ⚡️ FAST PATH: Pass the message + dynamic prompt directly to the LLM
        async def direct_llm_stream():
            try:
                db_history = request.history or []

                if request.conversation_id:
                    save_message(request.conversation_id, "user", request.message)

                messages = [{"role": "system", "content": dynamic_system_prompt}]
                messages.extend(db_history)
                messages.append({"role": "user", "content": request.message})

                full_answer = ""
                for chunk in stream_llm(messages):
                    full_answer += chunk
                    yield sse_data(chunk)
                yield sse_data("__END__")

                if request.conversation_id:
                    save_message(request.conversation_id, "assistant", full_answer)
            except Exception as e:
                yield sse_data(f"LLM Error: {str(e)}")
                yield sse_data("__END__")
        return StreamingResponse(direct_llm_stream(), media_type="text/event-stream")

    if request.conversation_id:
        save_message(request.conversation_id, "user", request.message)

    async def generator():
        async for chunk in generate_response_stream(
            user=request.message,
            retriever=retriever,
            conversation_id=request.conversation_id,
            history=request.history,
            selected_documents=request.selected_documents,
            user_id=current_user["user_id"],
            image_path=None,
        ):
            yield sse_data(chunk)
        yield sse_data("__END__")

    return StreamingResponse(generator(), media_type="text/event-stream")

@router.post("/chat/image")
def chat_image(
    message: str = Form(...),
    image: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    selected_documents: Optional[List[str]] = Form(None),
    current_user=Depends(get_current_user),
):
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())
    image_info = ImageStorage.save_image(file=image, conversation_id=conversation_id)

    result = generate_response(
        user=message,
        retriever=retriever,
        conversation_id=conversation_id,
        history=None,
        selected_documents=selected_documents,
        user_id=current_user["user_id"],
        image_path=image_info["path"],
    )
    return ChatResponse(response=result["answer"], sources=result["sources"])

@router.post("/chat/image/stream")
async def chat_image_stream(
    message: str = Form(...),
    image: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    selected_documents: Optional[List[str]] = Form(None),
    current_user=Depends(get_current_user),
):
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())
    image_info = ImageStorage.save_image(file=image, conversation_id=conversation_id)

    async def generator():
        async for chunk in generate_response_stream(
            user=message,
            retriever=retriever,
            conversation_id=conversation_id,
            history=None,
            selected_documents=selected_documents,
            user_id=current_user["user_id"],
            image_path=image_info["path"],
        ):
            yield sse_data(chunk)
        yield sse_data("__END__")
        
    return StreamingResponse(generator(), media_type="text/event-stream")

@router.post("/cancel/{generation_id}")
def cancel_chat(generation_id: str):
    cancel_generation(generation_id)
    return {"status": "cancelled"}

# =====================================================================
# RAG PERSISTENT KNOWLEDGE DOCUMENT SERVICE
# =====================================================================
@router.post("/upload", response_model=UploadResponse)
def upload(
    file: UploadFile = File(...), 
    workspace_id: Optional[int] = Form(None), 
    collection_id: Optional[int] = Form(None),
    department: Optional[str] = Form(None),
    tags: Optional[str] = Form(None), # Comma separated tag IDs
    current_user=Depends(get_current_user), 
    db=Depends(get_db)
):
    user_id = current_user["user_id"]
    if workspace_id:
        from app.auth.permissions import check_workspace_permission
        from app.db.models import Workspace, Organization, Document, Tag
        from app.core.billing_config import TIER_LIMITS, check_limit
        
        check_workspace_permission(workspace_id, ["owner", "admin", "manager", "developer"], current_user, db)
        
        # Enforce Billing limits for Documents
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if workspace:
            org = db.query(Organization).filter(Organization.id == workspace.organization_id).first()
            if org:
                current_docs = db.query(Document).join(Workspace).filter(Workspace.organization_id == org.id).count()
                limits = TIER_LIMITS.get(org.billing_plan.lower(), TIER_LIMITS["free"])
                if not check_limit(current_docs, limits["max_documents"]):
                    raise HTTPException(status_code=402, detail="Document upload limit reached for current billing tier")
    
    # 1. Read bytes and upload directly to MinIO S3
    file_bytes = file.file.read()
    file.file.seek(0)
    object_key = f"user_{user_id}/{file.filename}"
    
    storage_service.upload_file(
        file_content=file_bytes,
        bucket="athena-documents",
        object_name=object_key,
        content_type=file.content_type or "application/pdf"
    )

    # 2. Write to a temporary file for RAG ingestion (PyPDFLoader needs a real file path)
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        from app.rag.ocr_engine import ocr_engine
        # Process images via OCR
        is_image = file.content_type in ["image/jpeg", "image/png", "image/tiff"]
        
        if is_image and ocr_engine.client:
            ocr_result = ocr_engine.analyze_invoice(file_bytes)
            if ocr_result:
                text_content = ocr_result["content"]
                # For images, we write the extracted OCR text to a tmp .txt file for standard RAG ingestion
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w") as tmp_txt:
                    tmp_txt.write(text_content)
                    os.unlink(tmp_path) # Clean up original pdf tmp
                    tmp_path = tmp_txt.name
                    
        # Ingest from the temporary local file path
        chunks = document_service.ingest(tmp_path, user_id=user_id)
    finally:
        os.unlink(tmp_path) # Clean up temp file

    # 3. Save standard DB tracking metrics (with versioning)
    version = 1
    if workspace_id:
        existing = db.query(Document).filter(
            Document.workspace_id == workspace_id, 
            Document.filename == file.filename
        ).order_by(Document.version.desc()).first()
        if existing:
            version = existing.version + 1
            # Optionally remove older versions from ChromaDB here
            # document_service.delete_document(file.filename, user_id)
            # Actually, keeping it simple: just bump version in DB.

    doc_id = add_document(
        user_id, 
        file.filename, 
        object_key=object_key, 
        workspace_id=workspace_id,
        collection_id=collection_id,
        department=department,
        version=version
    )

    if tags and workspace_id:
        tag_ids = [int(t.strip()) for t in tags.split(",") if t.strip().isdigit()]
        if tag_ids:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                found_tags = db.query(Tag).filter(Tag.id.in_(tag_ids), Tag.workspace_id == workspace_id).all()
                doc.tags.extend(found_tags)
                db.commit()

    return UploadResponse(filename=file.filename, chunks=chunks)

@router.get("/documents", response_model=DocumentsResponse)
def get_documents_endpoint(current_user=Depends(get_current_user), workspace_id: int | None = None):
    # Pass workspace_id to list_documents
    rows = list_documents(current_user["user_id"], workspace_id)
    return {"documents": [{"filename": row[1]} for row in rows]}

@router.delete("/documents/{filename}", response_model=DeleteResponse)
def delete_document(filename: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    user_id = current_user["user_id"]
    
    # Needs to check workspace_id of the document, but since the endpoint 
    # currently only uses user_id, we will assume ownership check. For full RBAC, 
    # it should verify the user has manager/admin in the doc's workspace.
    deleted = delete_document_by_user(filename, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from Vector store
    document_service.delete_document(filename, user_id)
    
    # Remove from MinIO
    object_key = f"user_{user_id}/{filename}"
    storage_service.delete_file("athena-documents", object_key)
    
    return DeleteResponse(success=True, filename=filename)

# =====================================================================
# SYSTEM CONVERSATIONAL HISTORIC ARCHIVE RECORD SCHEDULING
# =====================================================================
import time

@router.get("/conversations", response_model=ConversationsResponse)
def get_conversations(current_user=Depends(get_current_user), workspace_id: int | None = None):
    print(f"[{time.time()}] Starting get_conversations")
    start = time.time()
    conversations = list_conversations(current_user["user_id"], workspace_id)
    print(f"[{time.time()}] DB query took {time.time() - start} seconds")
    
    start2 = time.time()
    res = ConversationsResponse(conversations=[
        ConversationInfo(id=row[0], title=row[1], created_at=row[2]) for row in conversations
    ])
    print(f"[{time.time()}] Pydantic took {time.time() - start2} seconds")
    return res

@router.post("/conversations", response_model=NewConversationResponse)
def new_conversation(current_user=Depends(get_current_user), workspace_id: int | None = None):
    conversation_id = create_conversation(title="New Chat", user_id=current_user["user_id"], workspace_id=workspace_id)
    return NewConversationResponse(id=conversation_id, title="New Chat")

@router.get("/conversations/search")
def search_chat_history(query: str, current_user=Depends(get_current_user), workspace_id: int | None = None):
    conversations = search_conversations(query, current_user["user_id"], workspace_id)
    return {"conversations": [{"id": row[0], "title": row[1], "created_at": row[2]} for row in conversations]}

@router.get("/conversations/{conversation_id}", response_model=MessagesResponse)
def get_conversation_messages(conversation_id: int, current_user=Depends(get_current_user)):
    owner = get_conversation_owner(conversation_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if owner[0] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")    

    messages = get_messages(conversation_id)
    return MessagesResponse(messages=[MessageInfo(role=row[0], content=row[1]) for row in messages])

@router.put("/conversations/{conversation_id}/title")
def update_title(conversation_id: int, request: UpdateTitleRequest, current_user=Depends(get_current_user)):
    owner = get_conversation_owner(conversation_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if owner[0] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    update_conversation_title(conversation_id, request.title)
    return {"success": True}

@router.delete("/conversations/{conversation_id}")
def remove_conversation(conversation_id: int, current_user=Depends(get_current_user)):
    delete_conversation(conversation_id, current_user["user_id"])
    return {"success": True}

@router.post("/conversations/clear-all")
def clear_all_conversations(current_user=Depends(get_current_user)):
    try:
        user_conversations = list_conversations(current_user["user_id"])
        for row in user_conversations:
            delete_conversation(conversation_id=row[0], user_id=current_user["user_id"])
        return {"success": True, "detail": f"Successfully cleared {len(user_conversations)} records."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Purge operational failure: {str(e)}")

# =====================================================================
# SPRINT 19 & 20 — HIGH-THROUGHPUT EXPENSE & AUTOMATION PIPELINE
# =====================================================================
@router.post("/ml/predict-expense", response_model=ExpensePredictionResponse, status_code=status.HTTP_200_OK)
async def predict_expense(payload: ExpensePredictionRequest):
    if not payload.descriptions:
        raise HTTPException(status_code=400, detail="Payload descriptions list cannot be empty.")
    try:
        if expense_tool is None:
            raise HTTPException(status_code=503, detail="Classifier model environment failed to initialize.")
        raw_predictions = [expense_tool.execute(desc) for desc in payload.descriptions]
        formatted_predictions = [
            SinglePredictionResult(
                category=pred.get("category", "Unassigned Operations"), 
                confidence=round(pred.get("confidence", 0.0), 4)
            )
            for pred in raw_predictions
        ]
        return ExpensePredictionResponse(status="success", predictions=formatted_predictions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference execution error: {str(e)}")

@router.post("/document-ai/process", response_model=StructuredDocumentPayload)
async def process_document_automation(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF artifacts supported.")

    upload_dir = Path("storage/temp_uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
    
    try:
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        raw_lines = []
        try:
            with pdfplumber.open(temp_file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        raw_lines.extend([line.strip() for line in text.split("\n") if line.strip()])
        except Exception as e:
            print(f"[PARSER LOG] Primary layout reader skipped: {e}")
            
        if not raw_lines:
            with open(temp_file_path, "rb") as f:
                content = f.read()
                found_strings = re.findall(b'\(([^)]+)\)', content)
                for string_bytes in found_strings:
                    try:
                        decoded_str = string_bytes.decode("utf-8", errors="ignore").strip()
                        if len(decoded_str) > 3 and not decoded_str.startswith("/"):
                            raw_lines.append(decoded_str)
                    except Exception:
                        continue
                        
        enriched_records = []
        for line in raw_lines:
            category = "Unassigned Operations"
            confidence = 0.0
            if expense_tool:
                try:
                    prediction = expense_tool.execute(line)
                    if isinstance(prediction, dict):
                        category = prediction.get("category", "Unassigned Operations")
                        confidence = prediction.get("confidence", 0.0)
                except Exception as e:
                    print(f"[CLASSIFIER LOG] Line processing skipped: {e}")
            
            pct_val = confidence * 100 if confidence <= 1.0 else confidence
            enriched_records.append(
                EnrichedLedgerItem(
                    raw_text=line,
                    predicted_category=category,
                    confidence_score=f"{pct_val:.1f}%"
                )
            )
        if temp_file_path.exists():
            temp_file_path.unlink()
        return StructuredDocumentPayload(
            total_lines_processed=len(enriched_records),
            enriched_records=enriched_records
        )
    except Exception as outer_err:
        if temp_file_path.exists():
            temp_file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Document AI Pipeline Runtime Failure: {str(outer_err)}")

# =====================================================================
# DEVELOPMENT PROFILE DIAGNOSTICS
# =====================================================================
@router.get("/test/filepicker", response_class=HTMLResponse)
def test_filepicker():
    html = """
    <!doctype html>
    <html>
        <head>
            <meta charset="utf-8" /><title>File Picker Test</title>
            <style> body { background: #0b1120; color: #e2e8f0; font-family: sans-serif; padding: 2rem; } .box { background: #0f172a; padding: 1.5rem; border-radius: 12px; }</style>
        </head>
        <body>
            <div class="box">
                <h2>Native File Picker Test</h2>
                <p>Click the button below to open the system file picker.</p>
                <label for="file" id="openBtn" style="display:inline-block;padding:0.6rem 1rem;border-radius:8px;background:#3b82f6;color:#fff;cursor:pointer">Open file picker</label>
                <input id="file" type="file" style="position:absolute;left:-9999px;opacity:0;" />
                <div id="out" style="margin-top:1rem;color:#94a3b8"></div>
            </div>
            <script>
                const fileInput = document.getElementById('file');
                const out = document.getElementById('out');
                document.getElementById('openBtn').addEventListener('click', function(){ fileInput.click(); });
                fileInput.addEventListener('change', function(){
                    out.textContent = this.files.length ? `Selected: ${this.files[0].name}` : 'No file selected';
                });
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html)