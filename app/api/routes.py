from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from app.auth.security import verify_password
from app.auth.jwt_handler import create_access_token
from app.memory.database import get_user_by_username
from fastapi import Depends
from app.utils.image_storage import ImageStorage
from fastapi import Form
import uuid
from app.auth.dependencies import get_current_user
from app.api.models import (
    LoginRequest,
    LoginResponse
)
from app.core.cancellation import cancel_generation
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
from ..services.chat_service import (
    generate_response,
    generate_response_stream,
)
from ..rag.retriever import Retriever

from fastapi import UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
import shutil
import json
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
    create_document,
    list_documents_by_user,
    delete_document_by_user,
    owns_document,    
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


def sse_data(chunk: str) -> str:
    if chunk == "__END__":
        return f"data: {chunk}\n\n"
    if chunk.startswith("__GENERATION_ID__:"):
        return f"data: {chunk}\n\n"
    return f"data: {json.dumps(chunk)}\n\n"


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
        current_user["user_id"],
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
@router.post("/chat/stream")
def chat_stream(
    request: ChatRequest,
    current_user=Depends(get_current_user),
):

    def generator():
        for chunk in generate_response_stream(
            user=request.message,
            retriever=retriever,
            conversation_id=request.conversation_id,
            history=request.history,
            selected_documents=request.selected_documents,
            user_id=current_user["user_id"],
            image_path=None,
        ):

            print("FASTAPI:", repr(chunk))

            yield sse_data(chunk)

        print("Sending END marker")

        yield sse_data("__END__")

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
    )
    
@router.post("/upload", response_model=UploadResponse)
def upload(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    documents_dir = Path(
        f"documents/user_{user_id}"
    )

    documents_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    destination = (
        documents_dir / file.filename
    )

    with open(destination, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    chunks = document_service.ingest(
        str(destination),
        user_id=user_id
    )

    create_document(
        user_id,
        file.filename
    )

    return UploadResponse(
        filename=file.filename,
        chunks=chunks,
    )
@router.get(
    "/documents",
    response_model=DocumentsResponse,
)
def list_documents(
    current_user=Depends(get_current_user)
):

    rows = list_documents_by_user(
        current_user["user_id"]
    )

    return DocumentsResponse(
        documents=[
            DocumentInfo(
                filename=row[0]
            )
            for row in rows
        ]
    )
@router.delete(
    "/documents/{filename}",
    response_model=DeleteResponse,
)
def delete_document(
    filename: str,
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    deleted = delete_document_by_user(
        filename,
        user_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    document_service.delete_document(
        filename,
        user_id
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
            db_stats["documents"],

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
@router.post("/cancel/{generation_id}")
def cancel_chat(generation_id: str):

    cancel_generation(generation_id)

    return {
        "status": "cancelled"
    }
@router.post("/chat/image")
def chat_image(
    message: str = Form(...),
    image: UploadFile = File(...),
    conversation_id: str | None = Form(None),
    selected_documents: list[str] | None = Form(None),
    current_user=Depends(get_current_user),
):
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())
    image_info = ImageStorage.save_image(
        file=image,
        conversation_id=conversation_id,
    )

    result = generate_response(
        user=message,
        retriever=retriever,
        conversation_id=conversation_id,
        history=None,
        selected_documents=selected_documents,
        user_id=current_user["user_id"],
        image_path=image_info["path"],
    )

    return ChatResponse(
        response=result["answer"],
        sources=result["sources"],
    )
@router.post("/chat/image/stream")
def chat_image_stream(
    message: str = Form(...),
    image: UploadFile = File(...),
    conversation_id: str | None = Form(None),
    selected_documents: list[str] | None = Form(None),
    current_user=Depends(get_current_user),
):
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    image_info = ImageStorage.save_image(
        file=image,
        conversation_id=conversation_id,
    )

    def generator():
        
        for chunk in generate_response_stream(
            user=message,
            retriever=retriever,
            conversation_id=conversation_id,
            history=None,
            selected_documents=selected_documents,
            user_id=current_user["user_id"],
            image_path=image_info["path"],
        ):

            print("FASTAPI:", repr(chunk))

            yield sse_data(chunk)

        print("Sending END marker")

        yield sse_data("__END__")
        
    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
    )


@router.get("/test/filepicker", response_class=HTMLResponse)
def test_filepicker():
        html = """
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8" />
                <title>File Picker Test</title>
                <style> body { background: #0b1120; color: #e2e8f0; font-family: sans-serif; padding: 2rem; } .box { background: #0f172a; padding: 1.5rem; border-radius: 12px; }</style>
            </head>
            <body>
                <div class="box">
                    <h2>Native File Picker Test</h2>
                    <p>Click the button below to open the system file picker. This page is a minimal test outside Streamlit.</p>
                      <label for="file" id="openBtn" style="display:inline-block;padding:0.6rem 1rem;border-radius:8px;background:#3b82f6;border:none;color:#fff;cursor:pointer">Open file picker</label>
                      <input id="file" type="file" style="position:absolute;left:-9999px;opacity:0;" />
                    <div id="out" style="margin-top:1rem;color:#94a3b8"></div>
                </div>
                <script>
                    const fileInput = document.getElementById('file');
                    const out = document.getElementById('out');
                    // Label-with-for will trigger the native picker directly; keep click() fallback
                    document.getElementById('openBtn').addEventListener('click', function(e){
                        try {
                            // allow browser to handle label activation; also call click() as fallback
                            fileInput.click();
                            console.log('Triggered input.click()');
                        } catch(err) {
                            console.error('click() failed', err);
                            out.textContent = 'Error triggering file picker: ' + err;
                        }
                    });
                    fileInput.addEventListener('change', function(e){
                        if(this.files && this.files.length) {
                            out.textContent = `Selected: ${this.files[0].name}`;
                            console.log('File selected:', this.files[0].name);
                        } else {
                            out.textContent = 'No file selected';
                        }
                    });
                    window.addEventListener('error', function(e){
                        console.error('Window error', e.error || e.message);
                    });
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=html)


@router.get("/test/filepicker-visible", response_class=HTMLResponse)
def test_filepicker_visible():
        html = """
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8" />
                <title>Visible File Picker Test</title>
                <meta name="viewport" content="width=device-width,initial-scale=1" />
            </head>
            <body style="font-family: system-ui, -apple-system, sans-serif; padding:24px;">
                <h2>Visible File Picker Test</h2>
                <p>Click the input below or the button to open the native file picker.</p>
                <input id="file" type="file" style="display:block;margin:12px 0;padding:8px;font-size:16px;" />
                <button id="btn" style="padding:8px 12px;font-size:16px;">Trigger input.click()</button>
                <pre id="log" style="margin-top:18px;color:#444"></pre>
                <script>
                    function log(s) {
                        var out = document.getElementById('log');
                        if (out) {
                            out.textContent = out.textContent + s + String.fromCharCode(10);
                        }
                    }
                    var btn = document.getElementById('btn');
                    var fileInput = document.getElementById('file');
                    if (btn && fileInput) {
                        btn.onclick = function() {
                            log('button click handler - calling input.click()');
                            try { fileInput.click(); } catch (err) { log('click() error: ' + err); }
                        };
                        fileInput.onclick = function() { log('input clicked'); };
                        fileInput.onchange = function(e) { log('files selected: ' + (e.target.files ? e.target.files.length : 0)); };
                    }
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=html)