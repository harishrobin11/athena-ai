from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Collection, Tag, Document
from app.auth.permissions import check_workspace_permission

router = APIRouter()

# =====================================================================
# REQUEST/RESPONSE SCHEMAS
# =====================================================================
class CollectionCreate(BaseModel):
    name: str
    workspace_id: int

class CollectionResponse(BaseModel):
    id: int
    name: str
    workspace_id: int
    created_at: datetime
    
class TagCreate(BaseModel):
    name: str
    color: Optional[str] = "#3b82f6"
    workspace_id: int

class TagResponse(BaseModel):
    id: int
    name: str
    color: str
    workspace_id: int

# =====================================================================
# COLLECTIONS
# =====================================================================
@router.post("/collections", response_model=CollectionResponse)
def create_collection(request: CollectionCreate, current_user=Depends(get_current_user), db=Depends(get_db)):
    check_workspace_permission(request.workspace_id, ["owner", "admin", "manager", "developer"], current_user, db)
    collection = Collection(name=request.name, workspace_id=request.workspace_id)
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection

@router.get("/collections/{workspace_id}", response_model=List[CollectionResponse])
def get_collections(workspace_id: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    check_workspace_permission(workspace_id, ["owner", "admin", "manager", "developer", "viewer", "analyst"], current_user, db)
    collections = db.query(Collection).filter(Collection.workspace_id == workspace_id).all()
    return collections

# =====================================================================
# TAGS
# =====================================================================
@router.post("/tags", response_model=TagResponse)
def create_tag(request: TagCreate, current_user=Depends(get_current_user), db=Depends(get_db)):
    check_workspace_permission(request.workspace_id, ["owner", "admin", "manager", "developer"], current_user, db)
    tag = Tag(name=request.name, color=request.color, workspace_id=request.workspace_id)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@router.get("/tags/{workspace_id}", response_model=List[TagResponse])
def get_tags(workspace_id: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    check_workspace_permission(workspace_id, ["owner", "admin", "manager", "developer", "viewer", "analyst"], current_user, db)
    tags = db.query(Tag).filter(Tag.workspace_id == workspace_id).all()
    return tags

@router.post("/documents/{document_id}/tags/{tag_id}")
def add_tag_to_document(document_id: int, tag_id: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    check_workspace_permission(document.workspace_id, ["owner", "admin", "manager", "developer"], current_user, db)
    
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.workspace_id == document.workspace_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found in this workspace")
        
    if tag not in document.tags:
        document.tags.append(tag)
        db.commit()
        
    return {"success": True}

@router.delete("/documents/{document_id}/tags/{tag_id}")
def remove_tag_from_document(document_id: int, tag_id: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    check_workspace_permission(document.workspace_id, ["owner", "admin", "manager", "developer"], current_user, db)
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag in document.tags:
        document.tags.remove(tag)
        db.commit()
        
    return {"success": True}
