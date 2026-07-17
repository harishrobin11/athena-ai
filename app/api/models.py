"""
Athena EAIOS - API Transport & Data Validation Schemas
Module: app.api.models
Description: Enforces strict data payload parsing schemas using Pydantic,
             integrating organizational department assignments directly into the transport layer.
"""

import enum
from pydantic import BaseModel, EmailStr, Field

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
    message: str = Field(..., max_length=4000, description="The user's input message")
    history: list = Field(default=[], description="Previous conversation messages")
    conversation_id: int | None = Field(default=None, description="The ID of the conversation thread")
    selected_documents: list[str] = Field(default=[], description="Specific documents to query")
    workspace_id: int | None = Field(default=None, description="The target workspace ID")

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
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100, description="Password must be at least 8 characters")
    # NEW: Allows setting a team context during onboarding (defaults to PROCUREMENT)
    department: DepartmentRole = DepartmentRole.PROCUREMENT

class RegisterResponse(BaseModel):
    message: str
    
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    # NEW: Passes clearance context directly back to the Streamlit UI state
    department: str
    role: str = "analyst"