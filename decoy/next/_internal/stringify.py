"""Message string generation."""

import os
from typing import Iterable

from .values import (
    AttributeEvent,
    AttributeEventType,
    CallEvent,
    Event,
    EventEntry,
    MatchOptions,
    VerificationEntry,
)


def stringify_verify_failure(
    mock_name: str,
    match_options: MatchOptions,
    expected: Event,
    all_events: list[EventEntry],
) -> str:
    if match_options.times is not None:
        heading = f"Expected exactly {_count(match_options.times, 'call')}:"
    else:
        heading = "Expected at least 1 call:"

    return _join_lines(
        heading,
        f"1.\t{_stringify_event(mock_name, expected)}",
        (
            f"Found {_count(len(all_events), 'call')}{'.' if len(all_events) == 0 else ':'}"
        ),
        _stringify_event_list(mock_name, [entry.event for entry in all_events]),
    )


def stringify_verify_order_failure(
    verifications: list[VerificationEntry],
    all_events: list[EventEntry],
) -> str:
    return _join_lines(
        "Expected call sequence:",
        _stringify_verification_list(verifications),
        f"Found {_count(len(all_events), 'call')}:",
        _stringify_event_entry_list(all_events),
    )


def stringify_miscalled_stub(
    name: str,
    expected_events: list[Event],
    actual_event: CallEvent,
) -> str:
    return _join_lines(
        "Mock was called but no matching `when` found.",
        f"Found {_count(len(expected_events), 'stubbing')}:",
        _stringify_event_list(name, expected_events),
        "Found 1 call:",
        f"1.\t{_stringify_event(name, actual_event)}",
    )


def stringify_redundant_verify(
    name: str,
    event: Event,
) -> str:
    return _join_lines(
        "The same `called_with` arguments were used with both `when` and `verify`.",
        "This is redundant and probably a misuse of the mock.",
        f"\t{_stringify_event(name, event)}",
        "See https://michael.cousins.io/decoy/usage/errors-and-warnings/#redundantverifywarning",
    )


def _stringify_event(
    mock_name: str,
    event: Event,
    ignore_extra_args: bool = False,
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


def _stringify_event_list(mock_name: str, events: Iterable[Event]) -> str:
    """Stringify a sequence of mock events into an ordered list."""
    return _stringify_ordered_list(
        _stringify_event(mock_name, event) for event in events
    )


def _stringify_event_entry_list(event_entries: Iterable[EventEntry]) -> str:
    """Stringify a sequence of verifications into an ordered list."""
    return _stringify_ordered_list(
        _stringify_event(entry.mock.name, entry.event) for entry in event_entries
    )


def _stringify_verification_list(verifications: Iterable[VerificationEntry]) -> str:
    """Stringify a sequence of verifications into an ordered list."""
    events: list[tuple[str, Event]] = []

    for verification in verifications:
        times = verification.matcher.options.times
        if times is None:
            times = 1

        for _ in range(times):
            events.append((verification.mock.name, verification.matcher.event))

    return _stringify_ordered_list(
        _stringify_event(mock_name, event) for mock_name, event in events
    )


def _count(count: int, noun: str) -> str:
    """Count a given noun, pluralizing if necessary."""
    return f"{count} {noun}{'s' if count != 1 else ''}"


def _join_lines(*lines: str) -> str:
    """Join a list of lines with newline characters."""
    return os.linesep.join(lines).strip()


def _stringify_ordered_list(lines: Iterable[str]) -> str:
    return _join_lines(*(f"{i + 1}.\t{line}" for i, line in enumerate(lines)))
