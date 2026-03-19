"""
调度器模块
"""
import threading
from datetime import datetime

_scheduler = None
_lock = threading.Lock()


class SimpleScheduler:
    """简单调度器"""

    def __init__(self):
        self._running = False
        self._thread = None

    def start(self):
        if not self._running:
            self._running = True

    def shutdown(self):
        self._running = False


def get_scheduler() -> SimpleScheduler:
    global _scheduler
    with _lock:
        if _scheduler is None:
            _scheduler = SimpleScheduler()
    return _scheduler
