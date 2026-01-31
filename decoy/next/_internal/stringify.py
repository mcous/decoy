"""Message string generation."""

import os
from typing import Iterable

from .values import (
    AttributeEvent,
    AttributeEventType,
    Event,
    EventEntry,
    VerificationEntry,
)


def stringify_event(
    mock_name: str, event: Event, ignore_extra_args: bool = False
) -> str:
    """Stringify a call to something human readable."""
    if isinstance(event, AttributeEvent):
        if event.type == AttributeEventType.SET:
            return f"{mock_name} = {event.value}"
        elif event.type == AttributeEventType.DELETE:
            return f"del {mock_name}"

        # unused, attribute get events are not logged
        return mock_name  # pragma: no cover

    else:
        args_list = [repr(arg) for arg in event.args]
        kwargs_list = [f"{key}={val!r}" for key, val in event.kwargs.items()]
        extra_args_msg = (
            " - ignoring unspecified arguments" if ignore_extra_args else ""
        )

        return f"{mock_name}({', '.join(args_list + kwargs_list)}){extra_args_msg}"


def stringify_event_list(mock_name: str, events: Iterable[Event]) -> str:
    """Stringify a sequence of mock events into an ordered list."""
    return _stringify_ordered_list(
        stringify_event(mock_name, event) for event in events
    )


def stringify_event_entry_list(event_entries: Iterable[EventEntry]) -> str:
    """Stringify a sequence of verifications into an ordered list."""
    return _stringify_ordered_list(
        stringify_event(entry.mock.name, entry.event) for entry in event_entries
    )


def stringify_verification_list(verifications: Iterable[VerificationEntry]) -> str:
    """Stringify a sequence of verifications into an ordered list."""
    events: list[tuple[str, Event]] = []

    for verification in verifications:
        times = verification.matcher.options.times
        if times is None:
            times = 1

        for _ in range(times):
            events.append((verification.mock.name, verification.matcher.event))

    return _stringify_ordered_list(
        stringify_event(mock_name, event) for mock_name, event in events
    )


def count(count: int, noun: str) -> str:
    """Count a given noun, pluralizing if necessary."""
    return f"{count} {noun}{'s' if count != 1 else ''}"


def join_lines(*lines: str) -> str:
    """Join a list of lines with newline characters."""
    return os.linesep.join(lines).strip()


def _stringify_ordered_list(lines: Iterable[str]) -> str:
    return join_lines(*(f"{i + 1}.\t{line}" for i, line in enumerate(lines)))
