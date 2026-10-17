"""Bounded Hugging Face client. Only user-safe errors cross this boundary."""
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
DEFAULT_CANDIDATES = "auto|Qwen/Qwen3-4B-Instruct-2507,auto|meta-llama/Llama-3.1-8B-Instruct"
FRIENDLY = "Text generation is temporarily unavailable. Please try again in a minute."
_cooldown_until = {}
_lock = threading.Lock()
_RETRY_STATUS = {408, 429, 500, 502, 503, 504}


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
        if (sep and re.fullmatch(r"[a-z0-9-]+", provider)
                and re.fullmatch(r"[\w.-]+/[\w.-]+", model)):
            pair = (provider, model)
            if pair not in result:
                result.append(pair)
    return result[:4]


def generate(prompt, max_tokens=500, temperature=0.7):
    """Try healthy candidates with bounded retry scheduling.

    GEN_TIMEOUT bounds socket inactivity per request. GEN_TOTAL_TIMEOUT
    limits retry scheduling across candidates; an active socket can overrun it.
    Credentials, prompts and provider response bodies are never logged.
    """
    token = os.getenv("HUGGINGFACEHUB_API_TOKEN", "").strip()
    candidates = _candidates()
    if not token or token == "your_token_here" or not candidates:
        log.error("Generation configuration is missing or invalid")
        raise MistralError(FRIENDLY)
    deadline = time.monotonic() + _number("GEN_TOTAL_TIMEOUT", 45, 5, 120)
    with _lock:
        live = [c for c in candidates if _cooldown_until.get(c, 0) <= time.monotonic()]
    if not live:
        raise MistralError(FRIENDLY)
    for provider, model in live:
        for attempt in range(2):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MistralError(FRIENDLY)
            try:
                response = requests.post(
                    ENDPOINT,
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "model": model if provider == "auto" else f"{model}:{provider}",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                    timeout=min(_number("GEN_TIMEOUT", 18, 2, 60), remaining),
                )
                if response.ok:
                    try:
                        content = response.json()["choices"][0]["message"]["content"]
                        if isinstance(content, str) and content.strip():
                            return content.strip()
                    except (KeyError, IndexError, TypeError, ValueError):
                        pass
                    log.warning("Generation candidate %s returned invalid content", model)
                    break
                log.warning("Generation candidate %s status=%s", model, response.status_code)
                if response.status_code in {401, 402}:
                    with _lock:
                        for candidate in candidates:
                            _cooldown_until[candidate] = time.monotonic() + 60
                    raise MistralError(FRIENDLY)
                # A 403 may be model-specific; fallback can still succeed.
                if response.status_code not in _RETRY_STATUS:
                    break
            except requests.RequestException as exc:
                log.warning("Generation candidate %s failed (%s)", model, type(exc).__name__)
            if attempt == 0:
                time.sleep(min(0.5, max(0, deadline - time.monotonic())))
        with _lock:
            _cooldown_until[(provider, model)] = time.monotonic() + 60
    raise MistralError(FRIENDLY)
