"""Spy call handling."""
from typing import Any

from .spy_log import SpyLog
from .context_managers import ContextWrapper
from .spy_events import SpyCall, SpyEvent
from .stub_store import StubStore


class CallHandler:
    """An interface to handle calls to spies."""

    def __init__(self, spy_log: SpyLog, stub_store: StubStore) -> None:
        """Initialize the CallHandler with access to SpyEvents and Stubs."""
        self._spy_log = spy_log
        self._stub_store = stub_store

    def handle(self, call: SpyEvent) -> Any:
        """Handle a Spy's call, triggering stub behavior if necessary."""
        if not isinstance(call.payload, SpyCall):
            raise NotImplementedError("Property handling not implemented")

        behavior = self._stub_store.get_by_call(call)
        self._spy_log.push(call)

        if behavior is None:
            return None

        if behavior.error:
            raise behavior.error

        if behavior.action:
            return behavior.action(*call.payload.args, **call.payload.kwargs)

        if behavior.context_value:
            return ContextWrapper(behavior.context_value)

        return behavior.return_value
