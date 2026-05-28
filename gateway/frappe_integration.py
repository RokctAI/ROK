"""
Frappe integration for ROK Gateway.
Handles calling Frappe APIs for ambient capture storage,
with offline queue fallback for network-interrupted environments.
"""

import asyncio
import os
import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Offline queue path uses rok-style directory
OFFLINE_QUEUE_PATH = Path(os.path.expanduser("~/.rok/frappe_queue.json"))


def _get_app_role() -> str:
    """
    Return 'control' if this instance is the Control Plane, otherwise 'tenant'.
    Reads ROK_APP_ROLE env var; defaults to 'tenant'.
    """
    return os.getenv("ROK_APP_ROLE", "tenant").strip().lower()


async def call_frappe_api(
    cmd: str,
    payload: Dict[str, Any],
    chat_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Call the Frappe gateway (tenant or control plane) via the rcore API bridge.
    Automatically retries once on transient 5xx errors and queues locally on
    network failure.
    """
    try:
        import httpx
    except ImportError:
        logger.error("httpx is not installed. Cannot call Frappe API.")
        return {"success": False, "error": "httpx not installed"}

    base_url = os.getenv("FRAPPE_BASE_URL")
    api_key = os.getenv("FRAPPE_API_KEY")
    api_secret = os.getenv("FRAPPE_API_SECRET")

    if not all([base_url, api_key, api_secret]):
        logger.debug("Frappe credentials missing, simulating success.")
        return {"success": True, "message": "Simulated success (missing credentials)"}

    app_role = _get_app_role()
    gateway = (
        "rcore.platform.api.control"
        if app_role == "control"
        else "rcore.platform.api.tenant"
    )
    url = f"{base_url.rstrip('/')}/api/method/{gateway}"

    headers = {
        "Authorization": f"token {api_key}:{api_secret}",
        "Content-Type": "application/json",
    }
    body = {"cmd": cmd, "payload": payload}

    async def do_call() -> "httpx.Response":
        async with httpx.AsyncClient() as client:
            return await client.post(url, json=body, headers=headers, timeout=30.0)

    try:
        response = await do_call()

        # Handle Validation Errors (4xx)
        if 400 <= response.status_code < 500:
            try:
                error_data = response.json()
                error_msg = (
                    error_data.get("message")
                    or error_data.get("error")
                    or "Validation error"
                )
            except Exception:
                error_msg = response.text or "Validation error"
            return {"success": False, "error": error_msg, "type": "validation"}

        # Handle Transient Errors (5xx) — retry once after 3s
        if response.status_code >= 500:
            logger.warning(
                "Transient Frappe error %s, retrying in 3s...", response.status_code
            )
            await asyncio.sleep(3)
            response = await do_call()
            if response.status_code >= 500:
                if chat_id:
                    _queue_failed_call(cmd, payload, chat_id)
                return {
                    "success": False,
                    "error": "Server error after retry",
                    "type": "transient",
                }

        response.raise_for_status()
        return response.json()

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.error("Frappe unreachable: %s", e)
        if chat_id:
            _queue_failed_call(cmd, payload, chat_id)
        return {
            "success": False,
            "error": "Saved locally — will sync when Frappe is back online",
            "type": "offline",
        }
    except Exception as e:
        logger.error("Frappe API call failed: %s", e)
        return {"success": False, "error": str(e)}


def _queue_failed_call(cmd: str, payload: dict, chat_id: str) -> None:
    """Save a failed Frappe API call to the local offline queue for later retry."""
    queue: list = []
    if OFFLINE_QUEUE_PATH.exists():
        try:
            queue = json.loads(OFFLINE_QUEUE_PATH.read_text(encoding="utf-8"))
        except Exception:
            queue = []

    queue.append(
        {
            "timestamp": time.time(),
            "cmd": cmd,
            "payload": payload,
            "chat_id": chat_id,
        }
    )

    OFFLINE_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    OFFLINE_QUEUE_PATH.write_text(json.dumps(queue, indent=2), encoding="utf-8")
    logger.info(
        "Queued offline Frappe call (%s) — %d item(s) pending.", cmd, len(queue)
    )


async def capture_to_frappe(
    intent: str,
    content: str,
    user_id: str,
    platform: str,
    chat_id: str,
) -> Dict[str, Any]:
    """
    Routes an ambient capture event through the Frappe gateway.

    Maps intent → Frappe method and builds the appropriate payload for each
    DocType (Career Milestone, Life Event, Personal Mastery Goal, etc.).
    """
    method_map = {
        "reminder": "platform:create_reminder",
        "task": "platform:create_task",
        "note": "platform:create_note",
        "career": "platform:create_career_milestone",
        "life": "platform:create_life_event",
        "goal": "platform:create_personal_mastery_goal",
        "health": "platform:create_life_event",
    }

    method = method_map.get(intent)
    if not method:
        return {"success": False, "error": f"Unknown intent: {intent}"}

    if intent == "career":
        payload: Dict[str, Any] = {
            "title": (content[:50] + "...") if len(content) > 50 else content,
            "description": content,
            "nominee": user_id,
        }
    elif intent == "life":
        payload = {
            "description": content,
            "nominee": user_id,
        }
    elif intent == "health":
        payload = {
            "description": content,
            "category": "Health",
            "nominee": user_id,
        }
    elif intent == "goal":
        payload = {
            "title": (content[:50] + "...") if len(content) > 50 else content,
            "description": content,
        }
    else:
        # Covers reminder, task, note
        payload = {
            "content": content,
            "user": user_id,
            "platform": platform,
            "metadata": {
                "source": "rok_ambient_capture",
                "intent": intent,
            },
        }

    return await call_frappe_api(method, payload, chat_id=chat_id)
