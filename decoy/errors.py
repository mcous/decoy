"""Error value objects."""
from typing import Optional, Sequence

from .call_stack import SpyCall, SpyRehearsal
from .stringify import stringify_error_message, count


class VerifyError(AssertionError):
    """An error raised when actual calls do not match rehearsals given to `verify`."""

    def __init__(
        self,
        rehearsals: Sequence[SpyRehearsal],
        calls: Sequence[SpyCall],
        times: Optional[int],
    ) -> None:
        """Initialize the error object and its message."""
        if times is not None:
            heading = f"Expected exactly {count(times, 'call')}:"
        elif len(rehearsals) == 1:
            heading = "Expected at least 1 call:"
        else:
            heading = "Expected call sequence:"

        message = stringify_error_message(
            heading=heading,
            rehearsals=rehearsals,
            calls=calls,
            include_calls=times is None,
        )

        super().__init__(message)
        self.rehearsals = rehearsals
        self.calls = calls
        self.times = times
