"""Error value objects."""
from typing import Optional, Sequence

from .spy import SpyCall, SpyRehearsal
from .stringify import stringify_error_message, count


class RehearsalNotFoundError(ValueError):
    """An error raised when `when` or `verify` is called without rehearsal(s)."""

    def __init__(self) -> None:
        super().__init__("Rehearsal not found for when/verify.")


class VerifyError(AssertionError):
    """An error raised when actual calls do not match rehearsals given to `verify`.

    Attributes:
        rehearsals: Rehearsals that were being verified.
        calls: Actual calls to the mock(s).
        times: The expected number of calls to the mock, if any.
    """

    rehearsals: Sequence[SpyRehearsal]
    calls: Sequence[SpyCall]
    times: Optional[int]

    def __init__(
        self,
        rehearsals: Sequence[SpyRehearsal],
        calls: Sequence[SpyCall],
        times: Optional[int],
    ) -> None:
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
