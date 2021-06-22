"""Rehearsed test double stub."""
from collections import deque
from typing import Deque, Generic, Optional

from .spy import SpyCall
from .types import ReturnT


class Stub(Generic[ReturnT]):
    """A rehearsed test double stub that may perform an action."""

    _rehearsal: SpyCall
    _values: Deque[ReturnT]
    _error: Optional[Exception]

    def __init__(self, rehearsal: SpyCall) -> None:
        """Initialize the stub from a rehearsal call.

        Arguments:
            rehearsal: A call tuple to match against.
        """
        self._rehearsal = rehearsal
        self._values = deque()
        self._error = None

    def then_return(self, *values: ReturnT) -> None:
        """Set the stub's return value(s).

        See [stubbing usage guide](../usage/when) for more details.

        Arguments:
            *values: Zero or more return values. Multiple values will result
                     in different return values for subsequent calls, with the
                     last value latching in once all other values have returned.
        """
        self._error = None
        self._values = deque(values)

    def then_raise(self, error: Exception) -> None:
        """Set the stub's error value.

        See [stubbing usage guide](../usage/when) for more details.

        Arguments:
            error: The error to raise.

        Note:
            Setting a stub to raise will prevent you from writing new
            rehearsals, because they will raise. If you need to make more calls
            to `when`, you'll need to wrap your rehearsal in a `try`.
        """
        self._value = None
        self._error = error

    def _act(self) -> Optional[ReturnT]:
        """Get the stub's value or raise its exception."""
        if self._error:
            raise self._error

        if len(self._values) == 0:
            return None
        elif len(self._values) == 1:
            return self._values[0]
        else:
            # if there is more than one value saved, shift off the queue
            return self._values.popleft()
