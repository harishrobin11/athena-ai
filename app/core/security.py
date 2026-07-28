# =====================================================================
# MULTI-TENANT BOUNDARY INTERCEPTOR (DICT-SAFE RESOLUTION)
# =====================================================================
from typing import List
from fastapi import HTTPException, Depends, status

# Import the token parser dependency from the sibling module
from app.auth.dependencies import get_current_user
from app.api.models import DepartmentRole

class DepartmentGuard:
    """Enforces organizational permission checks at the API gateway layer."""
    
    def __init__(self, allowed_departments: List[DepartmentRole]):
        # Store roles dynamically as a clean list of explicit string values
        self.allowed_departments = [d.value if hasattr(d, 'value') else d for d in allowed_departments]

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        """
        Intercepts the inbound current_user token dictionary payload and validates
        organizational scope bounds before granting database route access.
        """
        # Safely extract department context; default to PROCUREMENT if not explicitly flagged
        user_dept = current_user.get("department", "PROCUREMENT")
        
        # System Admin privilege tier naturally bypasses internal compartment partitions
        if user_dept == "ADMIN":
            return current_user
            
        if user_dept not in self.allowed_departments:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access Denied. Your tenant clearance profile ({user_dept}) "
                    f"lacks permission bounds to query resources scoped for this area."
                )
            )
            
        return current_user