"""One structured Gemini request per guide, conserving free-tier request quota."""
import json
import logging
import os
import re
import threading
import time
import requests
from utils.mistral import MistralError, FRIENDLY, _number

_log = logging.getLogger(__name__)
_lock = threading.Lock()
_cooldown_until = 0.0
KEYS = ("itinerary", "culture_tips", "packing_list")


def generate_guide(state, only=None):
    global _cooldown_until
    wanted = [key for key in KEYS if only is None or key in only]
    if not wanted:
        return {"generation_errors": []}
    token = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not token or token.startswith(("your_", "replace_")) or not re.fullmatch(r"gemini-[a-zA-Z0-9.-]+", model):
        raise MistralError(FRIENDLY)
    with _lock:
        if time.monotonic() < _cooldown_until:
            raise MistralError(FRIENDLY)
    instructions = {
        "itinerary": "Act as an itinerary planner. Write a practical two-day itinerary with morning, afternoon and evening activities, local food and a relaxed geographic route. Do not claim verified availability or prices.",
        "culture_tips": "Act as a cultural guide. Give concise, respectful local food, customs and etiquette tips. Avoid stereotypes and unsupported claims.",
        "packing_list": "Act as a packing adviser. Give a concise checklist grouped into clothing, gear, documents and essentials. Tailor it to the destination and travel preferences.",
    }
    prompt = json.dumps({
        "destination": state.get("top_destination"),
        "preferences": state.get("persona", []),
        "duration_days": 2,
        "tasks": {key: instructions[key] for key in wanted},
        "format": "Return a JSON object. Each requested key must contain a complete Markdown string, not a nested object. No external links. Weather is not a future forecast; do not invent weather or booking information.",
    })
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 2400,
            "thinkingConfig": {"thinkingBudget": 0},
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT", "properties": {key: {"type": "STRING"} for key in wanted},
                "required": wanted,
            },
        },
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    for attempt in range(2):
        try:
            response = requests.post(url, headers={"x-goog-api-key": token}, json=payload,
                                     timeout=_number("GEN_TIMEOUT", 35, 5, 60), allow_redirects=False)
        except requests.RequestException as exc:
            _log.warning("Gemini transport failed (%s)", type(exc).__name__)
            if attempt == 0:
                time.sleep(0.5)
                continue
            raise MistralError(FRIENDLY) from None
        if response.status_code == 429:
            with _lock:
                _cooldown_until = time.monotonic() + 60
            raise MistralError("The writing service has reached its current quota. Please try again later; your destination and weather results are saved.")
        if not response.ok:
            _log.warning("Gemini status=%s", response.status_code)
            if response.status_code in {500, 502, 503, 504} and attempt == 0:
                time.sleep(0.5)
                continue
            raise MistralError(FRIENDLY)
        try:
            candidate = response.json()["candidates"][0]
            if candidate.get("finishReason") not in (None, "STOP"):
                raise ValueError("Incomplete generation")
            text = "".join(p.get("text", "") for p in candidate["content"]["parts"] if not p.get("thought"))
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("Invalid guide object")
            result = {key: parsed.get(key, "").strip() if isinstance(parsed.get(key), str) else "" for key in wanted}
            result["generation_errors"] = [key for key in wanted if not result[key]]
            return result
        except (KeyError, IndexError, TypeError, ValueError):
            _log.warning("Gemini returned incomplete or invalid structured content")
            raise MistralError(FRIENDLY) from None
    raise MistralError(FRIENDLY)
