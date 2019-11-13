from typing import Protocol
from notifications import Notification


class _Factory(Protocol):
    def create(self, message: str, title: str, success: bool = True) -> Notification: pass


class _Backend(Protocol):
    def notify(self, n: Notification): pass


class Notify:
    """Handler to unconditionally emit a notification.

    This handler uses a _Backend to send a Notification created by the _Factory.
    """

    def __init__(self, factory: _Factory, backend: _Backend):
        self._factory = factory
        self._backend = backend

    def notify(self, message: str, title: str):
        self._backend.notify(self._factory.create(message=message, title=title))
