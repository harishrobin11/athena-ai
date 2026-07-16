from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class VaultDocument(BaseModel):
    id: str = Field(..., description="Unique document hash or identifier")
    content: str = Field(..., description="The raw textual memory or document chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata tags")

class VaultWriteRequest(BaseModel):
    documents: List[VaultDocument]

class VaultQueryRequest(BaseModel):
    query: str = Field(..., description="Semantic search query string")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of documents to retrieve")
    filter_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata filters")

class VaultResponse(BaseModel):
    success: bool
    count: int
    data: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)