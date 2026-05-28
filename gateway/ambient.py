"""
Ambient capture logic for ROK Gateway.
Classifies messages without wake phrases into Reminders, Notes, Tasks,
Career Milestones, Life Events, Goals, or Health logs.
"""

import logging
import json
import re
from typing import Optional, Dict, Any
from gateway.platforms.base import MessageEvent

logger = logging.getLogger(__name__)

# Intent patterns for classification (fallback if transformer is unavailable)
INTENT_PATTERNS = {
    "reminder": [
        r"remind me (to|about|that)",
        r"don't forget to",
        r"remember to",
        r"at \d{1,2}(:\d{2})?\s*(am|pm)?",
        r"in \d+ (minute|hour|day)",
    ],
    "task": [
        r"todo:",
        r"add task",
        r"i need to",
        r"task:",
        r"must do",
    ],
    "note": [
        r"note:",
        r"capture this:",
        r"save this",
        r"write down",
    ],
    "career": [
        r"milestone",
        r"promoted",
        r"promotion",
        r"career win",
        r"achieved",
        r"new job",
        r"started working at",
    ],
    "life": [
        r"life event",
        r"married",
        r"wedding",
        r"had a baby",
        r"moved to a new",
        r"bought a house",
        r"bought a car",
        r"graduated",
    ],
    "goal": [
        r"goal:",
        r"my goal is",
        r"set a goal",
        r"weekly goal",
        r"aim to",
        r"want to achieve",
    ],
    "health": [
        r"health:",
        r"weight:",
        r"blood pressure",
        r"symptoms",
        r"took my medication",
        r"workout:",
        r"exercise",
        r"slept",
        r"calories",
        r"heart rate",
    ]
}


async def classify_intent(text: str) -> str:
    """
    Classify the intent of the message.
    Uses Sentence Transformers if available, otherwise fallback to patterns.
    """
    try:
        from sentence_transformers import SentenceTransformer, util
        # Using a small, fast model for gateway classification.
        model = SentenceTransformer('all-MiniLM-L6-v2')

        choices = ["reminder", "task", "note", "career", "life", "goal", "health", "general chat"]
        text_emb = model.encode(text, convert_to_tensor=True)
        choice_embs = model.encode(choices, convert_to_tensor=True)

        scores = util.cos_sim(text_emb, choice_embs)[0]
        max_idx = scores.argmax().item()

        if scores[max_idx] > 0.4:
            return choices[max_idx]
    except Exception as e:
        logger.debug("SentenceTransformer classification failed, using patterns: %s", e)

    lowered = text.lower()
    for intent, patterns in INTENT_PATTERNS.items():
        if any(re.search(p, lowered) for p in patterns):
            return intent

    return "general chat"


async def handle_ambient_capture(runner, event: MessageEvent) -> Optional[str]:
    """
    Handles messages that did not trigger the wake phrase.
    Classifies intent and prompts user to confirm before saving.
    """
    text = event.text.strip()
    if not text:
        return None

    intent = await classify_intent(text)

    if intent == "general chat":
        # Ignore non-intent ambient noise
        return None

    # Get the adapter for this platform
    adapter = runner.adapters.get(event.source.platform)

    if not adapter:
        return None

    # Confirmation message
    confirmation_msg = (
        f"💡 I've detected a *{intent}*. Should I capture this?\n\n"
        f"> {text}\n\n"
        f'Reply with "yes" to confirm, or ignore to skip.'
    )

    # Store pending approval in session store
    session_key = runner._session_key_for_source(event.source)
    runner._pending_approvals[session_key] = {
        "type": "ambient_capture",
        "intent": intent,
        "content": text,
        "event": event
    }

    await adapter.send(event.source.chat_id, confirmation_msg)
    return None


async def process_confirmed_capture(runner, session_key: str, choice: str) -> Optional[str]:
    """
    Processes a capture after user confirms it with "yes".
    """
    pending = runner._pending_approvals.pop(session_key, None)
    if not pending or pending.get("type") != "ambient_capture":
        return None

    if choice.lower() != "yes":
        return "Okay, I've ignored that capture."

    intent = pending["intent"]
    content = pending["content"]
    event = pending["event"]

    from gateway.frappe_integration import capture_to_frappe
    result = await capture_to_frappe(
        intent=intent,
        content=content,
        user_id=event.source.user_id,
        platform=event.source.platform.value,
        chat_id=event.source.chat_id,
    )

    success = result.get("success", False)

    if success:
        if intent == "reminder":
            # Schedule a ROK cron job for the reminder delivery
            try:
                from cron.jobs import create_job
                # Heuristic time parsing from content
                schedule = "1h"
                if "minute" in content:
                    match = re.search(r"(\d+)\s*minute", content)
                    if match:
                        schedule = f"{match.group(1)}m"
                elif "hour" in content:
                    match = re.search(r"(\d+)\s*hour", content)
                    if match:
                        schedule = f"{match.group(1)}h"

                create_job(
                    prompt=f"Pinging you about your reminder: {content}",
                    schedule=schedule,
                    name=f"Reminder: {content[:20]}",
                    repeat=1,
                    deliver="origin",
                    origin=event.source.to_dict()
                )
            except Exception as e:
                logger.error("Failed to schedule reminder cron job: %s", e)

            return "✅ Reminder set! I'll ping you here when it's time."
        elif intent == "task":
            return "✅ Task added to your list."
        elif intent == "career":
            return "✅ Career Milestone logged successfully!"
        elif intent == "life":
            return "✅ Life Event logged successfully!"
        elif intent == "goal":
            return "✅ Personal Mastery Goal set successfully!"
        elif intent == "health":
            return "✅ Health event logged successfully!"
        else:
            return "✅ Note saved."
    else:
        error_type = result.get("type", "")
        if error_type == "offline":
            return f"📥 Saved locally — will sync when the backend is back online."
        elif error_type == "validation":
            return f"⚠️ Could not save {intent}: {result.get('error', 'Validation error')}."
        else:
            return f"⚠️ I tried to save that {intent}, but had trouble connecting to the backend. Please try again later!"
