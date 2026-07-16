"""
Athena EAIOS - API Transport & Data Validation Schemas
Module: app.api.models
Description: Enforces strict data payload parsing schemas using Pydantic,
             integrating organizational department assignments directly into the transport layer.
"""

import enum
from pydantic import BaseModel, EmailStr

# =====================================================================
# CORE ENTERPRISE SECURITY ENUMS
# =====================================================================
class DepartmentRole(str, enum.Enum):
    """Defines isolated business segments for data residency and access controls."""
    FINANCE = "FINANCE"
    PROCUREMENT = "PROCUREMENT"
    ADMIN = "ADMIN"

# =====================================================================
# SYSTEM CHAT & CORE ASSISTANT DATA SCHEMAS
# =====================================================================
class ChatRequest(BaseModel):
    message: str
    history: list = []
    conversation_id: int | None = None
    selected_documents: list[str] = []
    workspace_id: int | None = None

# =====================================================================
# MULTI-TENANT & RBAC SCHEMAS
# =====================================================================
class WorkspaceResponse(BaseModel):
    id: int
    name: str

class OrganizationResponse(BaseModel):
    id: int
    name: str
    billing_plan: str
    role: str
    department: str
    workspaces: list[WorkspaceResponse] = []

class Source(BaseModel):
    filename: str
    page: int

class ChatResponse(BaseModel):
    response: str
    sources: list[Source]

# =====================================================================
# INGESTION & CORE INFRASTRUCTURE DATA SCHEMAS
# =====================================================================
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
    
# =====================================================================
# MULTI-TENANT AUTHENTICATION SCHEMAS (UPDATED FOR RBAC)
# =====================================================================
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    # NEW: Allows setting a team context during onboarding (defaults to PROCUREMENT)
    department: DepartmentRole = DepartmentRole.PROCUREMENT

class RegisterResponse(BaseModel):
    message: str
    
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    # NEW: Passes clearance context directly back to the Streamlit UI state
    department: str
    role: str = "analyst"