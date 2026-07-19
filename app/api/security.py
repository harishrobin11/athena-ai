"""
Athena AI - Enterprise Security (Sprint 55)
Audit Logs | SSO / Azure Entra ID OIDC | Secrets Management | Compliance
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
import os
import hashlib
import hmac

from app.core.logger import logger
from app.db.redis import redis_manager

router = APIRouter(prefix="/api/security", tags=["Security"])
bearer_scheme = HTTPBearer(auto_error=False)

# ─── Audit Log ─────────────────────────────────────────────────────────────────

AUDIT_KEY   = "athena:audit_log"
AUDIT_SECRET = os.getenv("AUDIT_HMAC_SECRET", "athena-audit-hmac-default-secret")
MAX_AUDIT   = 10_000   # Rolling window


class AuditEvent(BaseModel):
    id:         str
    timestamp:  str
    user_id:    str
    action:     str              # CREATE | READ | UPDATE | DELETE | LOGIN | LOGOUT | EXPORT | ADMIN_ACTION
    resource:   str              # documents | users | agents | billing | settings …
    resource_id: Optional[str]  = None
    ip_address: Optional[str]   = None
    user_agent: Optional[str]   = None
    details:    Optional[Dict[str, Any]] = None
    outcome:    str = "success"  # success | failure | denied
    hmac_sig:   Optional[str]   = None  # tamper-evident signature


def _sign_event(event_dict: dict) -> str:
    """Compute an HMAC-SHA256 over the canonical fields to detect tampering."""
    canonical = json.dumps({
        k: event_dict[k]
        for k in ["id", "timestamp", "user_id", "action", "resource", "outcome"]
        if k in event_dict
    }, sort_keys=True)
    return hmac.new(
        AUDIT_SECRET.encode(),
        canonical.encode(),
        hashlib.sha256
    ).hexdigest()


async def write_audit_event(
    user_id: str,
    action:  str,
    resource: str,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    outcome: str = "success",
):
    """Write a tamper-evident audit event to Redis. Call from any endpoint."""
    event = AuditEvent(
        id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
        outcome=outcome,
    )
    event_dict = event.model_dump()
    event_dict["hmac_sig"] = _sign_event(event_dict)
    client = redis_manager.get_client()
    if client:
        await client.lpush(AUDIT_KEY, json.dumps(event_dict))
        await client.ltrim(AUDIT_KEY, 0, MAX_AUDIT - 1)
    return event


def _verify_event(event_dict: dict) -> bool:
    """Verify HMAC signature — returns False if tampered."""
    stored_sig = event_dict.pop("hmac_sig", None)
    if not stored_sig:
        return False
    expected = _sign_event(event_dict)
    event_dict["hmac_sig"] = stored_sig  # restore
    return hmac.compare_digest(stored_sig, expected)


# ─── SSO / OIDC ────────────────────────────────────────────────────────────────

class SSOConfig(BaseModel):
    provider:      str = "azure"          # azure | google | okta | generic
    client_id:     Optional[str] = None
    tenant_id:     Optional[str] = None   # Azure Entra tenant
    oidc_issuer:   Optional[str] = None   # e.g. https://login.microsoftonline.com/<tid>/v2.0
    redirect_uri:  Optional[str] = None
    scopes:        List[str] = ["openid", "profile", "email"]
    enabled:       bool = False

SSO_KEY = "athena:sso_config"


async def _get_sso_config() -> SSOConfig:
    client = redis_manager.get_client()
    if client:
        raw = await client.get(SSO_KEY)
        if raw:
            try:
                return SSOConfig(**json.loads(raw))
            except Exception:
                pass
    # Fall back to environment variables
    return SSOConfig(
        provider="azure",
        client_id=os.getenv("AZURE_AD_CLIENT_ID"),
        tenant_id=os.getenv("AZURE_AD_TENANT_ID"),
        oidc_issuer=os.getenv("AZURE_AD_ISSUER"),
        redirect_uri=os.getenv("AZURE_AD_REDIRECT_URI"),
        enabled=bool(os.getenv("AZURE_AD_CLIENT_ID")),
    )


async def validate_oidc_token(token: str, config: SSOConfig) -> Optional[Dict]:
    """
    Validate an OIDC Bearer token against the configured provider.
    Returns the decoded claims dict on success, None on failure.
    Supports Azure Entra ID (via python-jose RS256 + JWKS).
    """
    try:
        import httpx
        from jose import jwt as jose_jwt, JWTError

        issuer  = config.oidc_issuer or f"https://login.microsoftonline.com/{config.tenant_id}/v2.0"
        jwks_url = f"{issuer}/keys" if not issuer.endswith("/keys") else issuer.replace("/v2.0", "/v2.0/keys")

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(jwks_url)
            jwks = resp.json()

        claims = jose_jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=config.client_id,
            issuer=issuer,
            options={"verify_at_hash": False},
        )
        return claims
    except Exception as e:
        logger.warning(f"OIDC token validation failed: {e}")
        return None


# ─── Secrets Management ────────────────────────────────────────────────────────

class SecretEntry(BaseModel):
    name: str
    value: str                 # returned masked in list endpoints
    source: str = "env"        # env | vault | redis
    last_rotated: Optional[str] = None


def _get_secret(name: str) -> Optional[str]:
    """
    Fetch a secret — checks Azure Key Vault first (if configured),
    then falls back to environment variables.
    """
    vault_url = os.getenv("AZURE_KEYVAULT_URL")
    if vault_url:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            credential = DefaultAzureCredential()
            kv_client  = SecretClient(vault_url=vault_url, credential=credential)
            secret = kv_client.get_secret(name)
            return secret.value
        except Exception as e:
            logger.debug(f"Key Vault secret '{name}' not found, trying env: {e}")
    return os.getenv(name)


WATCHED_SECRETS = [
    "OPENAI_API_KEY",
    "AZURE_AD_CLIENT_ID",
    "AZURE_SEARCH_KEY",
    "AZURE_STORAGE_CONNECTION_STRING",
    "DATABASE_URL",
    "JWT_SECRET_KEY",
    "SLACK_WEBHOOK_URL",
]


# ─── Compliance ────────────────────────────────────────────────────────────────

class ComplianceReport(BaseModel):
    generated_at: str
    period_days:  int
    total_events: int
    by_action:    Dict[str, int]
    by_outcome:   Dict[str, int]
    by_user:      Dict[str, int]
    failed_events: int
    sso_enabled:  bool
    secrets_configured: List[str]
    audit_integrity_ok: bool
    warnings:     List[str]


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.post("/audit", status_code=status.HTTP_201_CREATED)
async def log_audit_event(
    request: Request,
    user_id: str,
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    outcome: str = "success",
    details: Optional[Dict[str, Any]] = None,
):
    """Manually write an audit event (also called internally by the system)."""
    event = await write_audit_event(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=details,
        outcome=outcome,
    )
    return {"success": True, "event_id": event.id}


@router.get("/audit", response_model=List[Dict])
async def get_audit_log(
    limit: int = 100,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    outcome: Optional[str] = None,
):
    """
    Retrieve recent audit events with optional filters.
    Events are returned newest-first.
    """
    client = redis_manager.get_client()
    if not client:
        raise HTTPException(503, "Storage unavailable")

    raw = await client.lrange(AUDIT_KEY, 0, min(limit * 3, MAX_AUDIT) - 1)
    events = []
    for r in raw:
        try:
            data = json.loads(r)
            # Apply filters
            if user_id and data.get("user_id") != user_id:
                continue
            if action and data.get("action") != action:
                continue
            if outcome and data.get("outcome") != outcome:
                continue
            events.append(data)
            if len(events) >= limit:
                break
        except Exception:
            pass
    return events


@router.get("/audit/verify")
async def verify_audit_integrity(sample_size: int = 200):
    """
    Verify HMAC signatures on recent audit entries to detect tampering.
    Returns a pass/fail report.
    """
    client = redis_manager.get_client()
    if not client:
        raise HTTPException(503, "Storage unavailable")

    raw = await client.lrange(AUDIT_KEY, 0, sample_size - 1)
    total = len(raw)
    tampered = []
    for r in raw:
        try:
            data = json.loads(r)
            if not _verify_event(data):
                tampered.append(data.get("id", "unknown"))
        except Exception:
            pass

    return {
        "checked": total,
        "tampered": len(tampered),
        "integrity_ok": len(tampered) == 0,
        "tampered_ids": tampered[:10],
    }


@router.get("/sso/config", response_model=SSOConfig)
async def get_sso_config():
    """Get current SSO / OIDC configuration."""
    config = await _get_sso_config()
    # Mask client secret if present
    return config


@router.put("/sso/config")
async def update_sso_config(config: SSOConfig):
    """Update SSO / OIDC configuration."""
    client = redis_manager.get_client()
    if client:
        await client.set(SSO_KEY, config.model_dump_json())
    return {"success": True, "sso_enabled": config.enabled}


@router.post("/sso/validate-token")
async def validate_sso_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """
    Validate an SSO Bearer token against the configured OIDC provider.
    Returns decoded claims on success.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="No token provided")

    config = await _get_sso_config()
    if not config.enabled:
        raise HTTPException(status_code=400, detail="SSO not enabled")

    claims = await validate_oidc_token(credentials.credentials, config)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"valid": True, "claims": claims}


@router.get("/sso/login-url")
async def get_sso_login_url():
    """
    Generate the OIDC authorization URL for the configured provider.
    Returns the URL to redirect the user to for SSO login.
    """
    config = await _get_sso_config()
    if not config.enabled:
        raise HTTPException(status_code=400, detail="SSO not configured")

    if config.provider == "azure":
        base = f"https://login.microsoftonline.com/{config.tenant_id}/oauth2/v2.0/authorize"
    else:
        base = f"{config.oidc_issuer}/authorize"

    params = {
        "client_id": config.client_id,
        "response_type": "code",
        "redirect_uri": config.redirect_uri,
        "scope": " ".join(config.scopes),
        "response_mode": "form_post",
        "state": str(uuid.uuid4()),
    }
    from urllib.parse import urlencode
    url = f"{base}?{urlencode(params)}"
    return {"login_url": url, "provider": config.provider}


@router.get("/secrets/status")
async def secrets_status():
    """
    Check which secrets are configured (values masked).
    Shows source (env / Azure Key Vault).
    """
    vault_url = os.getenv("AZURE_KEYVAULT_URL")
    status_list = []
    for name in WATCHED_SECRETS:
        val = _get_secret(name)
        source = "vault" if vault_url and val else ("env" if val else "missing")
        status_list.append({
            "name": name,
            "configured": bool(val),
            "source": source,
            "masked_value": f"{'*' * 8}{val[-4:]}" if val and len(val) > 4 else ("set" if val else None),
        })
    return {"secrets": status_list, "vault_url": vault_url or "not configured"}


@router.get("/compliance/report", response_model=ComplianceReport)
async def get_compliance_report(period_days: int = 30):
    """
    Generate an enterprise compliance report covering:
    - Audit log volume and breakdown
    - HMAC integrity check
    - SSO status
    - Secrets configuration
    - Security warnings
    """
    client = redis_manager.get_client()
    events: List[dict] = []
    if client:
        raw = await client.lrange(AUDIT_KEY, 0, MAX_AUDIT - 1)
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        for r in raw:
            try:
                data = json.loads(r)
                ts = datetime.fromisoformat(data.get("timestamp", "1970-01-01"))
                if ts >= cutoff:
                    events.append(data)
            except Exception:
                pass

    by_action: Dict[str, int] = {}
    by_outcome: Dict[str, int] = {}
    by_user: Dict[str, int] = {}
    tampered_count = 0

    for e in events:
        by_action[e.get("action", "unknown")] = by_action.get(e.get("action", "unknown"), 0) + 1
        by_outcome[e.get("outcome", "unknown")] = by_outcome.get(e.get("outcome", "unknown"), 0) + 1
        by_user[e.get("user_id", "unknown")] = by_user.get(e.get("user_id", "unknown"), 0) + 1
        e_copy = dict(e)
        if not _verify_event(e_copy):
            tampered_count += 1

    sso_cfg  = await _get_sso_config()
    configured_secrets = [n for n in WATCHED_SECRETS if _get_secret(n)]

    warnings = []
    if not sso_cfg.enabled:
        warnings.append("SSO is not enabled — all users authenticate with local passwords.")
    if "JWT_SECRET_KEY" not in configured_secrets:
        warnings.append("JWT_SECRET_KEY is not set — using insecure default.")
    if tampered_count > 0:
        warnings.append(f"{tampered_count} audit events failed HMAC integrity check.")
    if not os.getenv("AZURE_KEYVAULT_URL"):
        warnings.append("Azure Key Vault not configured — secrets sourced from environment variables.")
    if by_outcome.get("failure", 0) + by_outcome.get("denied", 0) > 50:
        warnings.append(f"High failure/denied event count: {by_outcome.get('failure', 0) + by_outcome.get('denied', 0)} — review access patterns.")

    return ComplianceReport(
        generated_at=datetime.utcnow().isoformat(),
        period_days=period_days,
        total_events=len(events),
        by_action=by_action,
        by_outcome=by_outcome,
        by_user=dict(sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:20]),
        failed_events=by_outcome.get("failure", 0) + by_outcome.get("denied", 0),
        sso_enabled=sso_cfg.enabled,
        secrets_configured=configured_secrets,
        audit_integrity_ok=tampered_count == 0,
        warnings=warnings,
    )
