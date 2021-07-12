"""Spy call handling."""
from typing import Any

from .call_stack import CallStack
from .stub_store import StubStore
from .spy_calls import SpyCall


class CallHandler:
    """An interface to handle calls to spies."""

    def __init__(self, call_stack: CallStack, stub_store: StubStore) -> None:
        """Initialize the CallHandler with access to SpyCalls and Stubs."""
        self._call_stack = call_stack
        self._stub_store = stub_store

    def handle(self, call: SpyCall) -> Any:
        """Handle a Spy's call, triggering stub behavior if necessary."""
        behavior = self._stub_store.get_by_call(call)
        self._call_stack.push(call)

        if behavior.error:
            raise behavior.error

        if behavior.action:
            return behavior.action(*call.args, **call.kwargs)

        return behavior.return_value
