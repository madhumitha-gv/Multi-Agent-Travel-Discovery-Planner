"""Process-wide admission control for the single-replica public demo.

This is deliberately not a durable billing limit. Use a shared gateway/store
before scaling to multiple replicas or sharing broadly.
"""
import threading
import time
from collections import deque
from utils.mistral import _number

_lock = threading.Lock()
_active = False
_starts = deque()


class LimitError(RuntimeError):
    pass


def admit(session_starts):
    global _active
    now = time.monotonic()
    with _lock:
        while _starts and now - _starts[0] >= 86400:
            _starts.popleft()
        recent = [t for t in session_starts if now - t < 3600]
        if len(recent) >= int(_number("SESSION_PLANS_PER_HOUR", 5, 1, 50)):
            raise LimitError("You've reached the demo limit for this hour. Please return later.")
        if len([t for t in _starts if now - t < 60]) >= int(_number("GLOBAL_PLANS_PER_MINUTE", 1, 1, 30)):
            raise LimitError("Please allow a minute between demo requests to protect the free API quota.")
        if _active:
            raise LimitError("Another trip is being planned. Please try again in a moment.")
        if len(_starts) >= int(_number("GLOBAL_PLANS_PER_DAY", 10, 1, 1000)):
            raise LimitError("The demo has reached its daily capacity. Please return later.")
        if len([t for t in _starts if now - t < 3600]) >= int(_number("GLOBAL_PLANS_PER_HOUR", 10, 1, 200)):
            raise LimitError("The demo has reached its hourly capacity. Please try again later.")
        _active = True
        _starts.append(now)
        return recent + [now]


def release():
    global _active
    with _lock:
        _active = False
