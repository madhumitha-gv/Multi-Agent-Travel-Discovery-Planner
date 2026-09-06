# logger.py
import queue

# Shared queue for log messages
log_queue = queue.Queue()

def log(message: str):
    """Push a log message to the queue for streaming."""
    log_queue.put(message)
