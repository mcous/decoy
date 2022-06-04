"""Message string generation."""
import os
from typing import Sequence

from .spy_events import AnySpyEvent, SpyCall, SpyEvent, SpyRehearsal, PropAccessType


def stringify_call(event: AnySpyEvent) -> str:
    """Stringify the call to something human readable.

    ```python
    SpyEvent(spy=SpyInfo(id=42, name="some_func"),
        payload=SpyCall(args=(1,), kwargs={"foo": False})
    )
    ```

    ...would stringify as `"some_func(1, foo=False)"`
    """
    spy, payload = event

    if not isinstance(payload, SpyCall):
        full_prop_name = f"{spy.name}.{payload.prop_name}"

        if payload.access_type == PropAccessType.SET:
            return f"{full_prop_name} = {payload.value}"
        elif payload.access_type == PropAccessType.DELETE:
            return f"del {full_prop_name}"

        return full_prop_name

    else:
        args_list = [repr(arg) for arg in payload.args]
        kwargs_list = [f"{key}={repr(val)}" for key, val in payload.kwargs.items()]
        extra_args_msg = (
            " - ignoring unspecified arguments" if payload.ignore_extra_args else ""
        )
        return f"{spy.name}({', '.join(args_list + kwargs_list)}){extra_args_msg}"


def stringify_call_list(calls: Sequence[AnySpyEvent]) -> str:
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
    rehearsals: Sequence[SpyRehearsal],
    calls: Sequence[SpyEvent],
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
