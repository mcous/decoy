"""Spy creation and storage."""
from typing import List, Sequence

from .spy import SpyCall, SpyRehearsal
from .errors import RehearsalNotFoundError


class CallStack:
    """SpyCall stack for all Spies in the Decoy container."""

    def __init__(self) -> None:
        """Initialize a stack for all SpyCalls."""
        self._stack: List[SpyCall] = []

    def push(self, spy_call: SpyCall) -> None:
        """Add a new spy call to the stack."""
        self._stack.append(spy_call)

    def consume_rehearsal(self) -> SpyRehearsal:
        """Consume the last call to a Spy as a rehearsal.

        This marks a call as a rehearsal but does not remove it from the stack.
        """
        return self.consume_rehearsals(count=1)[0]

    def consume_rehearsals(self, count: int) -> List[SpyRehearsal]:
        """Consume the last `count` calls to Spies as rehearsals.

        This marks calls as rehearsals but does not remove them from the stack.
        """
        calls = self._stack[-count:]

        if len(calls) != count or any(isinstance(call, SpyRehearsal) for call in calls):
            raise RehearsalNotFoundError()

        rehearsals = [SpyRehearsal(*call) for call in calls]
        self._stack[-count:] = rehearsals
        return rehearsals

    def get_by_rehearsals(self, rehearsals: Sequence[SpyRehearsal]) -> List[SpyCall]:
        """Get a list of all non-rehearsal calls to the given Spy IDs."""
        return [
            call
            for call in self._stack
            if not isinstance(call, SpyRehearsal)
            and any(rehearsal == call for rehearsal in rehearsals)
        ]

    def get_all(self) -> List[SpyCall]:
        """Get a list of all calls and rehearsals made."""
        return list(self._stack)

    def clear(self) -> None:
        """Remove all stored calls."""
        self._stack.clear()
