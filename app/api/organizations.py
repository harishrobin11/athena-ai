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

from app.api.models import MembersResponse, MemberResponse, InviteRequest, UpdateMemberRequest
from app.auth.permissions import OrgAdminGuard
from app.db.models import User

# Initialize the guard
admin_guard = OrgAdminGuard()

@router.get("/{org_id}/members", response_model=MembersResponse)
def get_organization_members(
    org_id: int,
    current_user: dict = Depends(admin_guard),
    db = Depends(get_db)
):
    # Fetch all users with a role in this org
    roles = db.query(UserRole).filter(UserRole.organization_id == org_id).all()
    members = []
    for r in roles:
        user = db.query(User).filter(User.id == r.user_id).first()
        if user:
            members.append(MemberResponse(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=r.role,
                department=r.department
            ))
    return MembersResponse(members=members)

@router.post("/{org_id}/invites")
def invite_user(
    org_id: int,
    request: InviteRequest,
    current_user: dict = Depends(admin_guard),
    db = Depends(get_db)
):
    # For MVP, we assume the user already exists by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with this email not found. (MVP requires existing users)")
        
    existing_role = db.query(UserRole).filter(
        UserRole.user_id == user.id,
        UserRole.organization_id == org_id
    ).first()
    
    if existing_role:
        raise HTTPException(status_code=400, detail="User is already in the organization.")
        
    new_role = UserRole(
        user_id=user.id,
        organization_id=org_id,
        role=request.role,
        department=request.department
    )
    db.add(new_role)
    db.commit()
    return {"success": True, "message": f"Added {user.email} to organization."}

@router.put("/{org_id}/members/{target_user_id}")
def update_member_role(
    org_id: int,
    target_user_id: int,
    request: UpdateMemberRequest,
    current_user: dict = Depends(admin_guard),
    db = Depends(get_db)
):
    user_role = db.query(UserRole).filter(
        UserRole.user_id == target_user_id,
        UserRole.organization_id == org_id
    ).first()
    
    if not user_role:
        raise HTTPException(status_code=404, detail="Member not found in organization.")
        
    if request.role:
        user_role.role = request.role
    if request.department:
        user_role.department = request.department
        
    db.commit()
    return {"success": True, "message": "Member updated successfully."}

@router.delete("/{org_id}/members/{target_user_id}")
def remove_member(
    org_id: int,
    target_user_id: int,
    current_user: dict = Depends(admin_guard),
    db = Depends(get_db)
):
    user_role = db.query(UserRole).filter(
        UserRole.user_id == target_user_id,
        UserRole.organization_id == org_id
    ).first()
    
    if not user_role:
        raise HTTPException(status_code=404, detail="Member not found in organization.")
        
    db.delete(user_role)
    db.commit()
    return {"success": True, "message": "Member removed from organization."}
