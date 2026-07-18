from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.auth.dependencies import get_current_user
from app.auth.permissions import check_workspace_permission
from app.db.database import get_db
from app.schemas.vault import VaultQueryRequest, VaultResponse, VaultWriteRequest, VaultDocument
from app.rag.vector_store import VectorStore
from langchain_core.documents import Document

router = APIRouter(prefix="/vault", tags=["AI Memory Vault"])
store = VectorStore()  # Instantiated once at backend component boundary

# =====================================================================
# SECURE SEMANTIC & HYBRID SEARCH ENDPOINT
# =====================================================================
@router.post("/query", response_model=VaultResponse)
async def query_memory(
    payload: VaultQueryRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    workspace_id = payload.workspace_id
    if not workspace_id:
        raise HTTPException(status_code=400, detail="Missing workspace_id boundary context.")
        
    check_workspace_permission(int(workspace_id), ["viewer"], current_user, db)
        
    try:
        filter_meta = payload.filter_metadata or {}
        filter_meta["workspace_id"] = workspace_id

        # Query the underlying partition
        matches = store.keyword_search(
            query=payload.query,
            limit=payload.top_k,
            filter_metadata=filter_meta
        )
        
        serialized_data = [
            {"content": match["document"], "metadata": match["metadata"], "score": match["keyword_score"]}
            for match in matches
        ]
        
        return VaultResponse(
            success=True,
            count=len(serialized_data),
            data=serialized_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid query sequence failed: {str(e)}")

# =====================================================================
# SECURE DATA INJECTION ENDPOINT (NEW)
# =====================================================================
@router.post("/inject")
async def inject_memory(
    payload: VaultWriteRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    workspace_id = payload.workspace_id
    if not workspace_id:
        raise HTTPException(status_code=400, detail="Missing workspace_id boundary context.")
        
    check_workspace_permission(int(workspace_id), ["developer"], current_user, db)
        
    try:
        # Wrap raw inputs into LangChain's Document schema
        docs_to_inject = [
            Document(
                page_content=doc.content,
                metadata={
                    **(doc.metadata or {}), 
                    "doc_id": doc.id,
                    "workspace_id": workspace_id  # Enforce the metadata security boundary tag
                }
            )
            for doc in payload.documents
        ]
        
        # Write directly to the dynamic partition store
        store.add_documents(docs_to_inject)
        
        return {
            "success": True, 
            "message": f"Successfully ingested {len(docs_to_inject)} documents into workspace '{workspace_id}'."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data injection failed: {str(e)}")