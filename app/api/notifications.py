"""
Athena AI - Notification System (Sprint 51)
In-app notifications with Slack webhook and email support.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.logger import logger
from app.db.redis import redis_manager
import json
import os

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

# ─── Models ────────────────────────────────────────────────────────────────────

class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "info"          # info | success | warning | error | agent
    user_id: Optional[str] = "global"
    source: Optional[str] = "system"
    action_url: Optional[str] = None

class Notification(BaseModel):
    id: str
    title: str
    message: str
    type: str
    user_id: str
    source: str
    action_url: Optional[str]
    read: bool = False
    created_at: str

class SlackWebhookPayload(BaseModel):
    webhook_url: str
    message: str
    title: Optional[str] = "Athena AI Notification"

class EmailPayload(BaseModel):
    to_email: str
    subject: str
    message: str

class NotificationSettings(BaseModel):
    slack_webhook_url: Optional[str] = None
    email_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None

# ─── Storage Helpers (Redis-backed) ────────────────────────────────────────────

NOTIFICATIONS_KEY = "athena:notifications"
SETTINGS_KEY = "athena:notification_settings"
MAX_NOTIFICATIONS = 100


async def _save_notification(n: Notification):
    client = redis_manager.get_client()
    if not client:
        return
    await client.lpush(NOTIFICATIONS_KEY, n.model_dump_json())
    await client.ltrim(NOTIFICATIONS_KEY, 0, MAX_NOTIFICATIONS - 1)


async def _get_notifications(user_id: Optional[str] = None, limit: int = 50) -> List[Notification]:
    client = redis_manager.get_client()
    if not client:
        return []
    raw = await client.lrange(NOTIFICATIONS_KEY, 0, limit - 1)
    notifications = []
    for r in raw:
        try:
            data = json.loads(r)
            n = Notification(**data)
            if user_id is None or n.user_id in (user_id, "global"):
                notifications.append(n)
        except Exception:
            pass
    return notifications


async def _mark_read(notification_id: str) -> bool:
    client = redis_manager.get_client()
    if not client:
        return False
    raw = await client.lrange(NOTIFICATIONS_KEY, 0, MAX_NOTIFICATIONS - 1)
    updated = False
    for i, r in enumerate(raw):
        try:
            data = json.loads(r)
            if data.get("id") == notification_id:
                data["read"] = True
                await client.lset(NOTIFICATIONS_KEY, i, json.dumps(data))
                updated = True
                break
        except Exception:
            pass
    return updated


async def _get_settings() -> NotificationSettings:
    client = redis_manager.get_client()
    if not client:
        return NotificationSettings()
    raw = await client.get(SETTINGS_KEY)
    if raw:
        try:
            return NotificationSettings(**json.loads(raw))
        except Exception:
            pass
    return NotificationSettings()


async def _save_settings(settings: NotificationSettings):
    client = redis_manager.get_client()
    if not client:
        return
    await client.set(SETTINGS_KEY, settings.model_dump_json())

# ─── Background Tasks ──────────────────────────────────────────────────────────

async def _send_slack(webhook_url: str, title: str, message: str):
    """Send notification to Slack via incoming webhook."""
    try:
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{title}*\n{message}"
                    }
                },
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"Athena AI • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"}]
                }
            ]
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=payload)
            if resp.status_code == 200:
                logger.info(f"Slack notification sent: {title}")
            else:
                logger.warning(f"Slack returned {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")


def _send_email_sync(settings: NotificationSettings, to_email: str, subject: str, message: str):
    """Send email notification via SMTP (sync, runs in background thread)."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.from_email or settings.smtp_user
        msg["To"] = to_email

        html = f"""
        <html><body style="font-family:sans-serif;background:#0B0F19;color:#e2e8f0;padding:24px;">
          <div style="max-width:600px;margin:auto;background:#1a2035;border-radius:12px;padding:32px;border:1px solid rgba(255,255,255,0.1);">
            <h1 style="color:#818cf8;margin:0 0 16px;">Athena AI</h1>
            <h2 style="margin:0 0 12px;">{subject}</h2>
            <p style="color:#94a3b8;line-height:1.6;">{message}</p>
            <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:24px 0;"/>
            <p style="color:#475569;font-size:12px;">Athena AI Enterprise Platform • Do not reply to this email.</p>
          </div>
        </body></html>
        """
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.from_email or settings.smtp_user, to_email, msg.as_string())
            logger.info(f"Email sent to {to_email}: {subject}")
    except Exception as e:
        logger.error(f"Email notification failed: {e}")

# ─── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=Notification, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: NotificationCreate,
    background_tasks: BackgroundTasks
):
    """Create a new in-app notification and optionally fan-out to Slack/Email."""
    n = Notification(
        id=str(uuid.uuid4()),
        title=payload.title,
        message=payload.message,
        type=payload.type,
        user_id=payload.user_id,
        source=payload.source,
        action_url=payload.action_url,
        read=False,
        created_at=datetime.utcnow().isoformat()
    )
    await _save_notification(n)

    # Fan-out: Slack
    settings = await _get_settings()
    if settings.slack_webhook_url:
        background_tasks.add_task(_send_slack, settings.slack_webhook_url, payload.title, payload.message)

    logger.info(f"Notification created: [{payload.type}] {payload.title}")
    return n


@router.get("/", response_model=List[Notification])
async def get_notifications(user_id: Optional[str] = "global", limit: int = 50):
    """Fetch latest notifications for a user."""
    return await _get_notifications(user_id=user_id, limit=limit)


@router.get("/unread-count")
async def unread_count(user_id: Optional[str] = "global"):
    """Return unread notification count for badge display."""
    notifications = await _get_notifications(user_id=user_id)
    count = sum(1 for n in notifications if not n.read)
    return {"count": count}


@router.patch("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """Mark a single notification as read."""
    updated = await _mark_read(notification_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.patch("/mark-all-read")
async def mark_all_read(user_id: Optional[str] = "global"):
    """Mark all notifications as read for a user."""
    client = redis_manager.get_client()
    if not client:
        return {"success": False}
    raw = await client.lrange(NOTIFICATIONS_KEY, 0, MAX_NOTIFICATIONS - 1)
    for i, r in enumerate(raw):
        try:
            data = json.loads(r)
            if data.get("user_id") in (user_id, "global"):
                data["read"] = True
                await client.lset(NOTIFICATIONS_KEY, i, json.dumps(data))
        except Exception:
            pass
    return {"success": True}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str):
    """Delete a notification by ID."""
    client = redis_manager.get_client()
    if not client:
        raise HTTPException(status_code=503, detail="Storage unavailable")
    raw = await client.lrange(NOTIFICATIONS_KEY, 0, MAX_NOTIFICATIONS - 1)
    for r in raw:
        try:
            data = json.loads(r)
            if data.get("id") == notification_id:
                await client.lrem(NOTIFICATIONS_KEY, 1, r)
                return {"success": True}
        except Exception:
            pass
    raise HTTPException(status_code=404, detail="Notification not found")


@router.post("/send-slack")
async def send_slack_notification(payload: SlackWebhookPayload, background_tasks: BackgroundTasks):
    """Manually send a Slack notification to a webhook URL."""
    background_tasks.add_task(_send_slack, payload.webhook_url, payload.title, payload.message)
    return {"success": True, "message": "Slack notification queued"}


@router.post("/send-email")
async def send_email_notification(payload: EmailPayload, background_tasks: BackgroundTasks):
    """Send an email notification using configured SMTP settings."""
    settings = await _get_settings()
    if not settings.smtp_host or not settings.smtp_user:
        raise HTTPException(status_code=400, detail="SMTP not configured. Set notification settings first.")
    background_tasks.add_task(_send_email_sync, settings, payload.to_email, payload.subject, payload.message)
    return {"success": True, "message": "Email queued"}


@router.get("/settings", response_model=NotificationSettings)
async def get_notification_settings():
    """Get current notification channel settings."""
    return await _get_settings()


@router.put("/settings")
async def update_notification_settings(settings: NotificationSettings):
    """Update Slack webhook URL and SMTP email settings."""
    await _save_settings(settings)
    return {"success": True, "message": "Notification settings updated"}
