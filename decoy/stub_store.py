"""Stub creation and storage."""
from typing import Any, Callable, List, NamedTuple, Optional, Union

from .spy_events import SpyEvent, WhenRehearsal, match_event


class _MISSING:
    pass


MISSING = _MISSING()
"""Value not specified sentinel.

Used when `None` could be a valid value,
so `Optional` would be inappropriate.
"""


class StubBehavior(NamedTuple):
    """A recorded stub behavior."""

    return_value: Optional[Any] = None
    context_value: Union[_MISSING, Any] = MISSING
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

    def add(
        self,
        rehearsal: WhenRehearsal,
        behavior: StubBehavior,
    ) -> None:
        """Create and add a new StubBehavior to the store."""
        self._stubs.append(StubEntry(rehearsal=rehearsal, behavior=behavior))

    def get_by_call(self, call: SpyEvent) -> Optional[StubBehavior]:
        """Get the latest StubBehavior matching this call."""
        reversed_indices = range(len(self._stubs) - 1, -1, -1)

        for i in reversed_indices:
            stub = self._stubs[i]

            if match_event(call, stub.rehearsal):
                if stub.behavior.once:
                    self._stubs.pop(i)

                return stub.behavior

        return None

    def clear(self) -> None:
        """Remove all stored Stubs."""
        self._stubs.clear()
