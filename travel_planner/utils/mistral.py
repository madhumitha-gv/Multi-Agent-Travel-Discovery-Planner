"""One generation boundary: Gemini first, Hugging Face fallback.

Agents keep calling generate(prompt, max_tokens, temperature). Only safe errors
cross this boundary; credentials, prompts and response bodies are never logged.
"""
import logging
import os
import re
import threading
import time

import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)
ENDPOINT = "https://router.huggingface.co/v1/chat/completions"
DEFAULT_CANDIDATES = "gemini|gemini-2.5-flash,auto|meta-llama/Llama-3.1-8B-Instruct"
FRIENDLY = "Text generation is temporarily unavailable. Please try again in a minute."
_cooldown_until = {}
_lock = threading.Lock()
_RETRY_STATUS = {408, 500, 502, 503, 504}


class MistralError(RuntimeError):
    """str(error) is safe to display to a visitor."""


def _number(name, default, low, high):
    try:
        return max(low, min(high, float(os.getenv(name, default))))
    except (ValueError, TypeError):
        return float(default)


def _candidates():
    result = []
    for item in os.getenv("GEN_CANDIDATES", DEFAULT_CANDIDATES).split(","):
        provider, sep, model = item.strip().partition("|")
        valid_model = (re.fullmatch(r"gemini-[a-zA-Z0-9.-]+", model) if provider == "gemini"
                       else re.fullmatch(r"[\w.-]+/[\w.-]+", model))
        if sep and re.fullmatch(r"[a-z0-9-]+", provider) and valid_model:
            if (provider, model) not in result:
                result.append((provider, model))
    return result[:4]


def _credential(provider):
    name = "GEMINI_API_KEY" if provider == "gemini" else "HUGGINGFACEHUB_API_TOKEN"
    token = os.getenv(name, "").strip()
    return "" if token.startswith(("your_", "replace_")) else token


def _call_candidate(provider, model, token, prompt, max_tokens, temperature, timeout):
    """Provider-specific encoding only; retry policy is shared below."""
    if provider == "gemini":
        return requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": token},
            json={
                "systemInstruction": {"parts": [{"text": f"Answer concisely and completely within {max_tokens} output tokens. Omit introductions and closing remarks."}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens,
                                     "thinkingConfig": {"thinkingBudget": 0}},
            }, timeout=timeout, allow_redirects=False,
        )
    return requests.post(
        ENDPOINT, headers={"Authorization": f"Bearer {token}"},
        json={"model": model if provider == "auto" else f"{model}:{provider}",
              "messages": [{"role": "user", "content": prompt}],
              "max_tokens": max_tokens, "temperature": temperature},
        timeout=timeout, allow_redirects=False,
    )


def _content(provider, response):
    try:
        data = response.json()
        if provider == "gemini":
            candidate = data["candidates"][0]
            if candidate.get("finishReason") not in (None, "STOP"):
                return None
            parts = candidate["content"]["parts"]
            content = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        else:
            content = data["choices"][0]["message"]["content"]
        return content.strip() if isinstance(content, str) and content.strip() else None
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return None


def _cool(candidate):
    with _lock:
        _cooldown_until[candidate] = time.monotonic() + 60


def generate(prompt, max_tokens=500, temperature=0.7):
    """Try candidates in order, preserving time for the fallback.

    At most two attempts per candidate. Quota, auth and billing failures fall
    through immediately. Network/5xx failures retry once with backoff. Socket
    timeouts bound inactivity, not an absolute wall-clock deadline.
    """
    candidates = _candidates()
    with _lock:
        live = [c for c in candidates if _cooldown_until.get(c, 0) <= time.monotonic()]
    deadline = time.monotonic() + _number("GEN_TOTAL_TIMEOUT", 75, 5, 120)
    for index, (provider, model) in enumerate(live):
        token = _credential(provider)
        if not token:
            _cool((provider, model))
            continue
        # Reserve a fair share of the remaining budget for later candidates.
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        candidate_deadline = time.monotonic() + remaining / (len(live) - index)
        for attempt in range(2):
            remaining = candidate_deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                response = _call_candidate(
                    provider, model, token, prompt, max_tokens, temperature,
                    min(_number("GEN_TIMEOUT", 20, 2, 60), remaining / (2 - attempt)),
                )
                if response.ok:
                    content = _content(provider, response)
                    if content:
                        return content
                    log.warning("Generation candidate %s returned invalid content", model)
                    break
                log.warning("Generation candidate %s status=%s", model, response.status_code)
                if response.status_code not in _RETRY_STATUS:
                    # Includes 429: do not waste quota or hold up the fallback.
                    break
            except requests.RequestException as exc:
                log.warning("Generation candidate %s failed (%s)", model, type(exc).__name__)
            if attempt == 0:
                time.sleep(min(0.5, max(0, candidate_deadline - time.monotonic())))
        _cool((provider, model))
    raise MistralError(FRIENDLY)
