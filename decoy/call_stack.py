"""Spy creation and storage."""
from typing import List, Sequence

from .spy_calls import BaseSpyCall, SpyCall, WhenRehearsal, VerifyRehearsal
from .errors import MissingRehearsalError


class CallStack:
    """SpyCall stack for all Spies in the Decoy container."""

    def __init__(self) -> None:
        """Initialize a stack for all SpyCalls."""
        self._stack: List[BaseSpyCall] = []

    def push(self, spy_call: SpyCall) -> None:
        """Add a new spy call to the stack."""
        self._stack.append(spy_call)

    def consume_when_rehearsal(self, ignore_extra_args: bool) -> WhenRehearsal:
        """Consume the last call to a Spy as a `when` rehearsal.

        This marks a call as a rehearsal but does not remove it from the stack.
        """
        try:
            call = self._stack[-1]
        except IndexError:
            raise MissingRehearsalError()
        if not isinstance(call, SpyCall):
            raise MissingRehearsalError()

        rehearsal = WhenRehearsal(*call)._replace(ignore_extra_args=ignore_extra_args)
        self._stack[-1] = rehearsal
        return rehearsal

    def consume_verify_rehearsals(
        self,
        count: int,
        ignore_extra_args: bool,
    ) -> List[VerifyRehearsal]:
        """Consume the last `count` calls to Spies as rehearsals.

        This marks calls as rehearsals but does not remove them from the stack.
        """
        calls = self._stack[-count:]

        if len(calls) != count or not all(isinstance(call, SpyCall) for call in calls):
            raise MissingRehearsalError()

        rehearsals = [
            VerifyRehearsal(*call)._replace(ignore_extra_args=ignore_extra_args)
            for call in calls
        ]
        self._stack[-count:] = rehearsals
        return rehearsals

    def get_by_rehearsals(self, rehearsals: Sequence[VerifyRehearsal]) -> List[SpyCall]:
        """Get all non-rehearsal calls to the spies in the given rehearsals."""
        return [
            call
            for call in self._stack
            if isinstance(call, SpyCall)
            and any(rehearsal.spy_id == call.spy_id for rehearsal in rehearsals)
        ]

    def get_all(self) -> List[BaseSpyCall]:
        """Get a list of all calls and rehearsals made."""
        return list(self._stack)

    def clear(self) -> None:
        """Remove all stored calls."""
        self._stack.clear()
