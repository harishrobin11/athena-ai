from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.permissions import OrgRBACGuard
from app.db.models import Organization
from pydantic import BaseModel

router = APIRouter(prefix="/billing", tags=["Billing & Subscriptions"])

class CheckoutRequest(BaseModel):
    plan: str

PLANS = [
    {"name": "free", "price": 0, "features": ["1 Workspace", "Basic RAG", "Community Support"]},
    {"name": "pro", "price": 49, "features": ["3 Workspaces", "Advanced AI Agents", "Email Support"]},
    {"name": "business", "price": 199, "features": ["Unlimited Workspaces", "Custom Agents", "Priority Support"]},
    {"name": "enterprise", "price": 999, "features": ["Dedicated Account Manager", "SSO", "On-Premise Deployment"]}
]

@router.get("/plans")
def get_plans():
    return {"success": True, "data": PLANS}

@router.get("/{org_id}/subscription")
def get_subscription(org_id: int, current_user=Depends(OrgRBACGuard(["owner", "admin"])), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    return {
        "success": True,
        "data": {
            "billing_plan": org.billing_plan,
            "status": org.subscription_status
        }
    }

@router.post("/{org_id}/checkout")
def create_checkout_session(org_id: int, request: CheckoutRequest, current_user=Depends(OrgRBACGuard(["owner"])), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    target_plan = next((p for p in PLANS if p["name"].lower() == request.plan.lower()), None)
    if not target_plan:
        raise HTTPException(status_code=400, detail="Invalid plan selected")
        
    # MOCK STRIPE GATEWAY
    # In a real scenario, this would call stripe.checkout.Session.create()
    mock_checkout_url = f"http://localhost:8501/?session_id=mock_{org_id}_{target_plan['name']}&success=true"
    
    # We will simulate the webhook synchronously for the MVP
    org.billing_plan = target_plan["name"]
    org.subscription_status = "active"
    db.commit()
    
    return {
        "success": True,
        "checkout_url": mock_checkout_url,
        "message": f"Successfully upgraded to {target_plan['name'].upper()} plan (Mocked)."
    }
