from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import MarketplaceItem, InstalledItem
from app.auth.permissions import check_workspace_permission

router = APIRouter()

# =====================================================================
# REQUEST/RESPONSE SCHEMAS
# =====================================================================
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: str # 'agent', 'prompt', 'workflow'
    payload: Optional[str] = None
    is_public: int = 1

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    type: str
    payload: Optional[str]
    author_id: Optional[int]
    is_public: int
    created_at: datetime
    installed: bool = False

class InstallRequest(BaseModel):
    workspace_id: int

# =====================================================================
# MARKETPLACE ENDPOINTS
# =====================================================================
@router.get("/items", response_model=List[ItemResponse])
def get_marketplace_items(workspace_id: Optional[int] = None, type: Optional[str] = None, current_user=Depends(get_current_user), db=Depends(get_db)):
    # 1. Fetch all public items
    query = db.query(MarketplaceItem).filter(MarketplaceItem.is_public == 1)
    if type:
        query = query.filter(MarketplaceItem.type == type)
    items = query.all()
    
    # 2. If workspace_id is provided, cross-reference with InstalledItems
    installed_ids = set()
    if workspace_id:
        check_workspace_permission(workspace_id, ["owner", "admin", "manager", "developer", "viewer", "analyst"], current_user, db)
        installed = db.query(InstalledItem).filter(InstalledItem.workspace_id == workspace_id).all()
        installed_ids = {i.item_id for i in installed}
        
    res = []
    for item in items:
        res.append(ItemResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            type=item.type,
            payload=item.payload,
            author_id=item.author_id,
            is_public=item.is_public,
            created_at=item.created_at,
            installed=item.id in installed_ids
        ))
    return res

@router.post("/items", response_model=ItemResponse)
def publish_item(request: ItemCreate, current_user=Depends(get_current_user), db=Depends(get_db)):
    # Simple check to see if user has elevated global role (in production this would check platform admin)
    if current_user.get("role") not in ["admin"]:
        raise HTTPException(status_code=403, detail="Only platform administrators can publish to the global marketplace.")
        
    item = MarketplaceItem(
        name=request.name,
        description=request.description,
        type=request.type,
        payload=request.payload,
        author_id=current_user["user_id"],
        is_public=request.is_public
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return ItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        type=item.type,
        payload=item.payload,
        author_id=item.author_id,
        is_public=item.is_public,
        created_at=item.created_at,
        installed=False
    )

@router.post("/items/{item_id}/install")
def install_item(item_id: int, request: InstallRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    # Must have developer or higher to install an agent to a workspace
    check_workspace_permission(request.workspace_id, ["owner", "admin", "manager", "developer"], current_user, db)
    
    item = db.query(MarketplaceItem).filter(MarketplaceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    # Check if already installed
    existing = db.query(InstalledItem).filter(
        InstalledItem.workspace_id == request.workspace_id,
        InstalledItem.item_id == item_id
    ).first()
    
    if existing:
        return {"status": "success", "message": "Item already installed"}
        
    installation = InstalledItem(workspace_id=request.workspace_id, item_id=item_id)
    db.add(installation)
    db.commit()
    
    return {"status": "success", "message": f"{item.name} installed successfully."}
