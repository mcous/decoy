"""Spy activity log."""
from typing import List, Sequence

from .errors import MissingRehearsalError
from .spy_events import (
    AnySpyEvent,
    SpyCall,
    SpyEvent,
    SpyPropAccess,
    WhenRehearsal,
    VerifyRehearsal,
    PropAccessType,
    PropRehearsal,
)


class SpyLog:
    """Log of all Spy activities in the Decoy container."""

    def __init__(self) -> None:
        self._log: List[AnySpyEvent] = []

    def push(self, spy_call: AnySpyEvent) -> None:
        """Add a new spy call to the stack."""
        self._log.append(spy_call)

    def consume_when_rehearsal(self, ignore_extra_args: bool) -> WhenRehearsal:
        """Consume the last call to a Spy as a `when` rehearsal.

        This marks a call as a rehearsal but does not remove it from the stack.
        """
        try:
            event = self._log[-1]
        except IndexError:
            raise MissingRehearsalError()
        if not isinstance(event, SpyEvent):
            raise MissingRehearsalError()

        spy, payload = _apply_ignore_extra_args(event, ignore_extra_args)

        rehearsal = WhenRehearsal(spy=spy, payload=payload)
        self._log[-1] = rehearsal
        return rehearsal

    def consume_verify_rehearsals(
        self,
        count: int,
        ignore_extra_args: bool,
    ) -> List[VerifyRehearsal]:
        """Consume the last `count` calls to Spies as rehearsals.

        This marks calls as rehearsals but does not remove them from the stack.
        """
        # events = self._log[-count:]
        rehearsals: List[VerifyRehearsal] = []
        index = len(self._log) - 1

        while len(rehearsals) < count:
            if index < 0:
                raise MissingRehearsalError()

            event = self._log[index]

            if not isinstance(event, (SpyEvent, PropRehearsal)):
                raise MissingRehearsalError()

            if _is_verifiable(event):
                rehearsal = VerifyRehearsal(
                    *_apply_ignore_extra_args(event, ignore_extra_args)
                )
                rehearsals.append(rehearsal)
                self._log[index] = rehearsal

            index = index - 1

        return list(reversed(rehearsals))

    def consume_prop_rehearsal(self) -> PropRehearsal:
        """Consume the last property get as a rehearsal."""
        try:
            event = self._log[-1]
        except IndexError:
            raise MissingRehearsalError()

        spy, payload = event

        if (
            not isinstance(event, SpyEvent)
            or not isinstance(payload, SpyPropAccess)
            or payload.access_type != PropAccessType.GET
        ):
            raise MissingRehearsalError()

        rehearsal = PropRehearsal(spy, payload)
        self._log[-1] = rehearsal
        return rehearsal

    def get_calls_to_verify(self, spy_ids: Sequence[int]) -> List[SpyEvent]:
        """Get all non-rehearsal calls to the spies in the given rehearsals."""
        return [
            event
            for event in self._log
            if event.spy.id in spy_ids
            and isinstance(event, SpyEvent)
            and _is_verifiable(event)
        ]

    def get_all(self) -> List[AnySpyEvent]:
        """Get a list of all calls and rehearsals made."""
        return list(self._log)

    def clear(self) -> None:
        """Remove all stored calls."""
        self._log.clear()


def _is_verifiable(event: AnySpyEvent) -> bool:
    return isinstance(event, SpyEvent) and (
        isinstance(event.payload, SpyCall)
        or event.payload.access_type != PropAccessType.GET
    )


def _apply_ignore_extra_args(event: AnySpyEvent, ignore_extra_args: bool) -> SpyEvent:
    spy, payload = event

    if isinstance(payload, SpyCall):
        payload = payload._replace(ignore_extra_args=ignore_extra_args)

    return SpyEvent(spy=spy, payload=payload)
