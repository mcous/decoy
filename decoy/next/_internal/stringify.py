"""Message string generation."""

import os
from typing import List

from .event import AttributeEvent, Event, EventAndState


def stringify_event(name: str, event: Event, ignore_extra_args: bool = False) -> str:
    """Stringify a call to something human readable."""
    if isinstance(event, AttributeEvent):
        return "TODO: attribute event"
        # full_prop_name = f"{spy.name}.{payload.prop_name}"

        # if payload.access_type == PropAccessType.SET:
        #     return f"{full_prop_name} = {payload.value}"
        # elif payload.access_type == PropAccessType.DELETE:
        #     return f"del {full_prop_name}"

        # return full_prop_name

    else:
        args_list = [repr(arg) for arg in event.args]
        kwargs_list = [f"{key}={val!r}" for key, val in event.kwargs.items()]
        extra_args_msg = (
            " - ignoring unspecified arguments" if ignore_extra_args else ""
        )

        return f"{name}({', '.join(args_list + kwargs_list)}){extra_args_msg}"


def stringify_event_list(name: str, events: List[EventAndState]) -> str:
    """Stringify a sequence of mock events into an ordered list."""
    return os.linesep.join(
        f"{i + 1}.\t{stringify_event(name, entry.event)}"
        for i, entry in enumerate(events)
    )


def count(count: int, noun: str) -> str:
    """Count a given noun, pluralizing if necessary."""
    return f"{count} {noun}{'s' if count != 1 else ''}"


def join_lines(*lines: str) -> str:
    """Join a list of lines with newline characters."""
    return os.linesep.join(lines).strip()


def stringify_error_message(
    heading: str,
    name: str,
    expected: Event,
    actual: List[EventAndState],
) -> str:
    """Stringify an error message about a rehearsals to calls comparison."""
    return join_lines(
        heading,
        stringify_event(name, expected),
        (f"Found {count(len(actual), 'call')}{'.' if len(actual) == 0 else ':'}"),
        stringify_event_list(name, actual),
    )
