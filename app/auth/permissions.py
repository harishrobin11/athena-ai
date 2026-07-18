from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import UserRole

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import UserRole, Workspace

class RBACGuard:
    """Enforces organizational permission checks based on allowed roles."""
    
    # Role hierarchy: lower index = higher privilege
    ROLE_HIERARCHY = ["owner", "admin", "manager", "developer", "viewer"]
    
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def _has_permission(self, user_role: str) -> bool:
        if user_role not in self.ROLE_HIERARCHY:
            return False
            
        user_rank = self.ROLE_HIERARCHY.index(user_role)
        # Check if the user's role is at least as privileged as any allowed role
        for allowed in self.allowed_roles:
            if allowed in self.ROLE_HIERARCHY:
                if user_rank <= self.ROLE_HIERARCHY.index(allowed):
                    return True
        return False
        
    def _verify_access(self, role: str):
        if not self._has_permission(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied. Required roles: {self.allowed_roles}"
            )

class OrgRBACGuard(RBACGuard):
    """Enforces RBAC when org_id is in the path parameters."""
    def __call__(self, request: Request, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
        user_id = current_user.get("user_id")
        org_id_str = request.path_params.get("org_id")
        if not org_id_str:
            raise HTTPException(status_code=400, detail="org_id path parameter is missing.")
            
        org_id = int(org_id_str)
        user_role = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.organization_id == org_id
        ).first()
        
        if not user_role:
            raise HTTPException(status_code=403, detail="User is not a member of this organization.")
            
        self._verify_access(user_role.role)
        return current_user

def check_workspace_permission(workspace_id: int, allowed_roles: list[str], current_user: dict, db: Session):
    """Utility function to check RBAC given a workspace_id manually inside an endpoint."""
    user_id = current_user.get("user_id")
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")
        
    user_role = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.organization_id == workspace.organization_id
    ).first()
    
    if not user_role:
        raise HTTPException(status_code=403, detail="User is not a member of the organization owning this workspace.")
        
    guard = RBACGuard(allowed_roles)
    guard._verify_access(user_role.role)

# Maintain backward compatibility for Sprint 26 endpoints
OrgAdminGuard = lambda: OrgRBACGuard(["owner", "admin"])
