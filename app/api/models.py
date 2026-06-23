from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    history: list = []
    conversation_id: int | None = None
    selected_documents: list[str] = []

class Source(BaseModel):
    filename: str
    page: int


class ChatResponse(BaseModel):
    response: str
    sources: list[Source]


class UploadResponse(BaseModel):
    chunks: int
    filename: str

class DocumentInfo(BaseModel):
    filename: str


class DocumentsResponse(BaseModel):
    documents: list[DocumentInfo]

class DeleteResponse(BaseModel):
    success: bool
    filename: str

class ConversationInfo(BaseModel):
    id: int
    title: str
    created_at: str


class ConversationsResponse(BaseModel):
    conversations: list[ConversationInfo]

class NewConversationResponse(BaseModel):
    id: int
    title: str

class UpdateTitleRequest(BaseModel):
    title: str
    
class MessageInfo(BaseModel):
    role: str
    content: str


class MessagesResponse(BaseModel):
    messages: list[MessageInfo]
    
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    message: str
    
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str