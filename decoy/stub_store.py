"""Stub creation and storage."""
from typing import Any, Callable, List, NamedTuple, Optional

from .spy_calls import SpyCall, WhenRehearsal


class StubBehavior(NamedTuple):
    """A recorded stub behavior."""

    return_value: Optional[Any] = None
    error: Optional[Exception] = None
    action: Optional[Callable[..., Any]] = None
    once: bool = False


class StubEntry(NamedTuple):
    """An entry in the StubStore for later behavior lookup."""

    rehearsal: WhenRehearsal
    behavior: StubBehavior


class StubStore:
    """Stored stub behaviors."""

    def __init__(self) -> None:
        """Initialize a StubStore with an empty stubbings list."""
        self._stubs: List[StubEntry] = []

    def add(self, rehearsal: WhenRehearsal, behavior: StubBehavior) -> None:
        """Create and add a new StubBehavior to the store."""
        self._stubs.append(StubEntry(rehearsal=rehearsal, behavior=behavior))

    def get_by_call(self, call: SpyCall) -> StubBehavior:
        """Get the latest StubBehavior matching this call."""
        reversed_indices = range(len(self._stubs) - 1, -1, -1)

        for i in reversed_indices:
            stub = self._stubs[i]

            if stub.rehearsal == call:
                if stub.behavior.once:
                    self._stubs.pop(i)

                return stub.behavior

        return StubBehavior()

    def clear(self) -> None:
        """Remove all stored Stubs."""
        self._stubs.clear()
