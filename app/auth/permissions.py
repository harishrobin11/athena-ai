from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import UserRole

class OrgAdminGuard:
    """Enforces organizational permission checks for Admins."""
    
    def __init__(self):
        pass

    def __call__(
        self,
        org_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        user_id = current_user.get("user_id")
        
        # Look for a user_role matching this user_id and org_id
        user_role = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.organization_id == org_id
        ).first()
        
        if not user_role or user_role.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Denied. You must be an organization administrator to perform this action."
            )
            
        return current_user
