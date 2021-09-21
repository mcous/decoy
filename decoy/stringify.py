"""Message string generation."""
import os
from typing import Sequence

from .spy_calls import BaseSpyCall, BaseSpyRehearsal, SpyCall


def stringify_call(call: BaseSpyCall) -> str:
    """Stringify the call to something human readable.

    `SpyCall(spy_id=42, spy_name="name", args=(1,), kwargs={"foo": False})`
    would stringify as `"name(1, foo=False)"`
    """
    args_list = [repr(arg) for arg in call.args]
    kwargs_list = [f"{key}={repr(val)}" for key, val in call.kwargs.items()]
    extra_args_msg = (
        " - ignoring unspecified arguments" if call.ignore_extra_args else ""
    )
    return f"{call.spy_name}({', '.join(args_list + kwargs_list)}){extra_args_msg}"


def stringify_call_list(calls: Sequence[BaseSpyCall]) -> str:
    """Stringify a sequence of calls into an ordered list."""
    return os.linesep.join(
        f"{i + 1}.\t{stringify_call(call)}" for i, call in enumerate(calls)
    )


def count(count: int, noun: str) -> str:
    """Count a given noun, pluralizing if necessary."""
    return f"{count} {noun}{'s' if count != 1 else ''}"


def join_lines(*lines: str) -> str:
    """Join a list of lines with newline characters."""
    return os.linesep.join(lines).strip()


def stringify_error_message(
    heading: str,
    rehearsals: Sequence[BaseSpyRehearsal],
    calls: Sequence[SpyCall],
    include_calls: bool = True,
) -> str:
    """Stringify an error message about a rehearsals to calls comparison."""
    return join_lines(
        heading,
        stringify_call_list(rehearsals),
        (
            f"Found {count(len(calls), 'call')}"
            f"{'.' if len(calls) == 0 or not include_calls else ':'}"
        ),
        stringify_call_list(calls) if include_calls else "",
    )
