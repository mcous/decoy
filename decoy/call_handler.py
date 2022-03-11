"""Spy call handling."""
from typing import Any, NamedTuple, Optional

from .spy_log import SpyLog
from .context_managers import ContextWrapper
from .spy_events import SpyCall, SpyEvent
from .stub_store import StubStore


class CallHandlerResult(NamedTuple):
    value: Any


class CallHandler:
    """An interface to handle calls to spies."""

    def __init__(self, spy_log: SpyLog, stub_store: StubStore) -> None:
        """Initialize the CallHandler with access to SpyEvents and Stubs."""
        self._spy_log = spy_log
        self._stub_store = stub_store

    def handle(self, call: SpyEvent) -> Optional[CallHandlerResult]:
        """Handle a Spy's call, triggering stub behavior if necessary."""
        behavior = self._stub_store.get_by_call(call)
        self._spy_log.push(call)

        if behavior is None:
            return None

        if behavior.error:
            raise behavior.error

        return_value: Any

        if behavior.action:
            if not isinstance(call.payload, SpyCall):
                raise NotImplementedError("Property handling not implemented")
            return_value = behavior.action(*call.payload.args, **call.payload.kwargs)

        elif behavior.context_value:
            return_value = ContextWrapper(behavior.context_value)

        else:
            return_value = behavior.return_value

        return CallHandlerResult(return_value)
