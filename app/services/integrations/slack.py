import httpx
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def dispatch_slack_message(webhook_url: str, text: str, blocks: list = None) -> bool:
    """
    Dispatches a message to a Slack incoming webhook.
    """
    payload = {"text": text}
    if blocks:
        payload["blocks"] = blocks
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                logger.info("Successfully dispatched message to Slack")
                return True
            else:
                logger.error(f"Failed to dispatch to Slack: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error dispatching Slack message: {e}")
        return False
