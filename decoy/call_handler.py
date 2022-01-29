"""Spy call handling."""
from typing import Any

from .spy_log import SpyLog
from .context_managers import ContextWrapper
from .spy_calls import SpyCall
from .stub_store import StubStore


class CallHandler:
    """An interface to handle calls to spies."""

    def __init__(self, spy_log: SpyLog, stub_store: StubStore) -> None:
        """Initialize the CallHandler with access to SpyCalls and Stubs."""
        self._spy_log = spy_log
        self._stub_store = stub_store

    def handle(self, call: SpyCall) -> Any:
        """Handle a Spy's call, triggering stub behavior if necessary."""
        behavior = self._stub_store.get_by_call(call)
        self._spy_log.push(call)

        if behavior is None:
            return None

        elif behavior.error:
            raise behavior.error

        elif behavior.action:
            return_value = behavior.action(*call.args, **call.kwargs)

        elif behavior.context_value:
            return_value = ContextWrapper(behavior.context_value)

        else:
            return_value = behavior.return_value

        return return_value
