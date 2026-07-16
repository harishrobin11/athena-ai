from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Organization, Workspace, UserRole
from app.api.models import OrganizationResponse, WorkspaceResponse

router = APIRouter(prefix="/orgs", tags=["Organizations"])

@router.get("", response_model=List[OrganizationResponse])
def get_user_organizations(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    user_id = current_user["user_id"]
    
    # Get all roles for the user
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    
    org_responses = []
    for role in user_roles:
        org = db.query(Organization).filter(Organization.id == role.organization_id).first()
        if not org:
            continue
            
        workspaces = db.query(Workspace).filter(Workspace.organization_id == org.id).all()
        
        org_responses.append(OrganizationResponse(
            id=org.id,
            name=org.name,
            billing_plan=org.billing_plan,
            role=role.role,
            department=role.department,
            workspaces=[WorkspaceResponse(id=w.id, name=w.name) for w in workspaces]
        ))
        
    return org_responses
