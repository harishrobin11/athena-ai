from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.auth.dependencies import DepartmentGuard
from app.schemas.vault import VaultQueryRequest, VaultResponse
from app.rag.vector_store import VectorStore
from langchain_core.documents import Document

router = APIRouter(prefix="/vault", tags=["AI Memory Vault"])
store = VectorStore()  # Instantiated once at backend component boundary

# =====================================================================
# SCHEMAS FOR DATA INGESTION
# =====================================================================
class DocumentItem(BaseModel):
    id: str
    content: str
    metadata: Optional[dict] = {}

class VaultWriteRequest(BaseModel):
    documents: List[DocumentItem]

# =====================================================================
# SECURE SEMANTIC & HYBRID SEARCH ENDPOINT
# =====================================================================
@router.post("/query", response_model=VaultResponse)
async def query_memory(
    payload: VaultQueryRequest,
    tenant_context: Dict[str, Any] = Depends(DepartmentGuard(allowed_departments=["ADMIN", "FINANCE", "PROCUREMENT"]))
):
    # Support both department context naming conventions safely
    dept_id = tenant_context.get("department") or tenant_context.get("dept_id")
    if not dept_id:
        raise HTTPException(status_code=400, detail="Missing department boundary context.")
        
    try:
        filter_meta = payload.filter_metadata or {}
        filter_meta["dept_id"] = dept_id

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
    tenant_context: Dict[str, Any] = Depends(DepartmentGuard(allowed_departments=["ADMIN", "FINANCE", "PROCUREMENT"]))
):
    dept_id = tenant_context.get("department") or tenant_context.get("dept_id")
    if not dept_id:
        raise HTTPException(status_code=400, detail="Missing department boundary context.")
        
    try:
        # Wrap raw inputs into LangChain's Document schema
        docs_to_inject = [
            Document(
                page_content=doc.content,
                metadata={
                    **(doc.metadata or {}), 
                    "doc_id": doc.id,
                    "dept_id": dept_id  # Enforce the metadata security boundary tag
                }
            )
            for doc in payload.documents
        ]
        
        # Write directly to the dynamic partition store
        store.add_documents(docs_to_inject)
        
        return {
            "success": True, 
            "message": f"Successfully ingested {len(docs_to_inject)} documents into partition '{dept_id}'."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data injection failed: {str(e)}")