"""Spy activity log."""
from typing import List, Sequence

from .errors import MissingRehearsalError
from .spy_events import BaseSpyEvent, SpyCall, SpyEvent, WhenRehearsal, VerifyRehearsal


class SpyLog:
    """Log of all Spy activities in the Decoy container."""

    def __init__(self) -> None:
        self._stack: List[BaseSpyEvent] = []

    def push(self, spy_call: SpyEvent) -> None:
        """Add a new spy call to the stack."""
        self._stack.append(spy_call)

    def consume_when_rehearsal(self, ignore_extra_args: bool) -> WhenRehearsal:
        """Consume the last call to a Spy as a `when` rehearsal.

        This marks a call as a rehearsal but does not remove it from the stack.
        """
        try:
            event = self._stack[-1]
        except IndexError:
            raise MissingRehearsalError()
        if not isinstance(event, SpyEvent):
            raise MissingRehearsalError()

        spy_id, spy_name, payload = _apply_ignore_extra_args(event, ignore_extra_args)

        rehearsal = WhenRehearsal(spy_id=spy_id, spy_name=spy_name, payload=payload)
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
        events = self._stack[-count:]

        if len(events) != count or not all(isinstance(e, SpyEvent) for e in events):
            raise MissingRehearsalError()

        rehearsals = [
            VerifyRehearsal(*_apply_ignore_extra_args(e, ignore_extra_args))
            for e in events
        ]
        self._stack[-count:] = rehearsals
        return rehearsals

    def get_by_rehearsals(
        self, rehearsals: Sequence[VerifyRehearsal]
    ) -> List[SpyEvent]:
        """Get all non-rehearsal calls to the spies in the given rehearsals."""
        return [
            call
            for call in self._stack
            if isinstance(call, SpyEvent)
            and any(rehearsal.spy_id == call.spy_id for rehearsal in rehearsals)
        ]

    def get_all(self) -> List[BaseSpyEvent]:
        """Get a list of all calls and rehearsals made."""
        return list(self._stack)

    def clear(self) -> None:
        """Remove all stored calls."""
        self._stack.clear()


def _apply_ignore_extra_args(
    event: BaseSpyEvent, ignore_extra_args: bool
) -> BaseSpyEvent:
    spy_id, spy_name, payload = event

    if isinstance(payload, SpyCall):
        payload = payload._replace(ignore_extra_args=ignore_extra_args)

    return BaseSpyEvent(spy_id=spy_id, spy_name=spy_name, payload=payload)
