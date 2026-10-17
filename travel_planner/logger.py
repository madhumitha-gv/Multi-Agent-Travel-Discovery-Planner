"""Request-local progress events propagated through LangGraph's context."""
from contextvars import ContextVar

_progress = ContextVar("trip_progress", default=None)


def bind_progress(callback):
    return _progress.set(callback)


def reset_progress(token):
    _progress.reset(token)


def log(message: str):
    callback = _progress.get()
    if callback:
        callback(str(message))
