from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from app.db.database import get_db
from app.auth.dependencies import get_current_user
from app.db.models import User, Organization, Workspace, Document, TokenUsage
import datetime

router = APIRouter(prefix="/admin", tags=["Admin Portal"])

def get_superadmin(current_user=Depends(get_current_user)):
    """Guard to ensure only SuperAdmins can access these routes."""
    # MVP approach: username == "admin" or department == "ADMIN"
    is_super = current_user.get("username") == "admin" or current_user.get("department") == "ADMIN"
    if not is_super:
        raise HTTPException(status_code=403, detail="SuperAdmin access required")
    return current_user

@router.get("/users")
def get_all_users(db=Depends(get_db), current_user=Depends(get_superadmin)):
    """Fetch all users across the platform."""
    users = db.query(User).all()
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "created_at": u.created_at.isoformat()
            } for u in users
        ]
    }

@router.get("/analytics")
def get_platform_analytics(db=Depends(get_db), current_user=Depends(get_superadmin)):
    """Aggregates system-wide usage."""
    total_users = db.query(User).count()
    total_orgs = db.query(Organization).count()
    total_workspaces = db.query(Workspace).count()
    total_docs = db.query(Document).count()
    
    # Calculate total tokens consumed across platform
    total_tokens_query = db.query(func.sum(TokenUsage.tokens)).scalar()
    total_tokens = total_tokens_query if total_tokens_query else 0

    return {
        "data": {
            "total_users": total_users,
            "total_orgs": total_orgs,
            "total_workspaces": total_workspaces,
            "total_documents": total_docs,
            "total_tokens_consumed": total_tokens
        }
    }

@router.get("/billing")
def get_all_billing(db=Depends(get_db), current_user=Depends(get_superadmin)):
    """Lists all organizations and their current subscription tiers."""
    orgs = db.query(Organization).all()
    return {
        "data": [
            {
                "id": o.id,
                "name": o.name,
                "billing_plan": o.billing_plan,
                "subscription_status": o.subscription_status,
                "created_at": o.created_at.isoformat()
            } for o in orgs
        ]
    }

@router.get("/logs")
def get_system_logs(current_user=Depends(get_superadmin)):
    """Simulated backend server logs for MVP."""
    now = datetime.datetime.utcnow()
    # Provide some realistic-looking logs
    logs = [
        f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] INFO: Athena AI Server started successfully",
        f"[{(now - datetime.timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S')}] INFO: Database connection pooled (max_size=20)",
        f"[{(now - datetime.timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')}] WARN: High memory usage detected in RAG pipeline",
        f"[{(now - datetime.timedelta(minutes=25)).strftime('%Y-%m-%d %H:%M:%S')}] INFO: Stripe webhook received (evt_1NgX)",
        f"[{(now - datetime.timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')}] ERROR: Failed to fetch metadata for Workspace ID 45"
    ]
    return {"logs": logs}
