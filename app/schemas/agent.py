from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class AgentEventType(str, Enum):
    NODE_START = "node_start"       # Entering an agent node (e.g., RAG Worker)
    NODE_END = "node_end"           # Exiting an agent node
    THOUGHT = "thought"             # Intermediate thinking reasoning steps
    TOKEN = "token"                 # LLM generation text tokens
    FINAL_RESPONSE = "final"        # Complete payload with source elements

class AgentStreamPayload(BaseModel):
    event_type: AgentEventType = Field(..., description="The type of event being streamed")
    node_name: Optional[str] = Field(None, description="The LangGraph node generating this event")
    content: Optional[str] = Field(None, description="Text chunk, thought string, or status message")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Contextual elements, sources, or tokens")

class AgentChatRequest(BaseModel):
    message: str = Field(..., example="Analyze our Q3 compliance risk.")
    department: Optional[str] = Field(None, example="FINANCE")
    tenant_id: Optional[str] = Field("default", example="1")
    workspace_id: Optional[str] = Field("default", example="1")
    selected_documents: Optional[list[str]] = Field(default=[], description="Selected document filenames")
