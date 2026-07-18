from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Workspace, UserRole, Organization
from app.api.models import WorkspaceResponse
from app.core.billing_config import TIER_LIMITS, check_limit

router = APIRouter(prefix="/orgs/{org_id}/workspaces", tags=["Workspaces"])

class WorkspaceCreate(BaseModel):
    name: str

@router.get("", response_model=List[WorkspaceResponse])
def get_org_workspaces(
    org_id: int,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    user_id = current_user["user_id"]
    
    # Verify user belongs to this org
    role = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.organization_id == org_id).first()
    if not role:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
        
    workspaces = db.query(Workspace).filter(Workspace.organization_id == org_id).all()
    return [WorkspaceResponse(id=w.id, name=w.name) for w in workspaces]

@router.post("", response_model=WorkspaceResponse)
def create_workspace(
    org_id: int,
    request: WorkspaceCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    user_id = current_user["user_id"]
    
    # Verify user belongs to this org and is an admin
    role = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.organization_id == org_id).first()
    if not role or role.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Only owners/admins can create workspaces")
        
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    current_workspaces = db.query(Workspace).filter(Workspace.organization_id == org_id).count()
    limits = TIER_LIMITS.get(org.billing_plan.lower(), TIER_LIMITS["free"])
    if not check_limit(current_workspaces, limits["max_workspaces"]):
        raise HTTPException(status_code=402, detail="Workspace limit reached for current billing tier")
        
    workspace = Workspace(organization_id=org_id, name=request.name)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return WorkspaceResponse(id=workspace.id, name=workspace.name)

@router.get("/{workspace_id}/metrics")
def get_workspace_metrics(
    org_id: int,
    workspace_id: int,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    from app.db.models import TokenUsage
    from sqlalchemy import func
    from app.services.cache import metrics_cache
    
    cache_key = f"metrics_{workspace_id}"
    cached_metrics = metrics_cache.get(cache_key)
    if cached_metrics:
        return cached_metrics
    
    # Optional: verify workspace belongs to org and user has access
    total_tokens = db.query(func.sum(TokenUsage.tokens)).filter(TokenUsage.workspace_id == workspace_id).scalar() or 0
    
    # Group by model
    model_stats = db.query(TokenUsage.model, func.sum(TokenUsage.tokens)).filter(
        TokenUsage.workspace_id == workspace_id
    ).group_by(TokenUsage.model).all()
    
    # Group by day
    from sqlalchemy.sql import cast
    from sqlalchemy import Date
    daily_stats = db.query(
        cast(TokenUsage.timestamp, Date).label("date"), 
        func.sum(TokenUsage.tokens).label("total")
    ).filter(
        TokenUsage.workspace_id == workspace_id
    ).group_by("date").order_by("date").all()
    
    result = {
        "total_tokens": total_tokens,
        "models": [{"model": m[0], "tokens": m[1]} for m in model_stats],
        "daily": [{"date": str(d.date), "tokens": d.total} for d in daily_stats]
    }
    metrics_cache.set(cache_key, result)
    return result

class IntegrationCreate(BaseModel):
    provider: str
    config_json: str

@router.post("/{workspace_id}/integrations")
def configure_integration(
    org_id: int,
    workspace_id: int,
    request: IntegrationCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    from app.db.models import IntegrationConfig
    user_id = current_user["user_id"]
    
    # Verify user is admin
    role = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.organization_id == org_id).first()
    if not role or role.role != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can configure integrations")
        
    existing = db.query(IntegrationConfig).filter(
        IntegrationConfig.workspace_id == workspace_id,
        IntegrationConfig.provider == request.provider
    ).first()
    
    if existing:
        existing.config_json = request.config_json
    else:
        new_config = IntegrationConfig(
            workspace_id=workspace_id,
            provider=request.provider,
            config_json=request.config_json
        )
        db.add(new_config)
        
    db.commit()
    return {"status": "success", "provider": request.provider}
