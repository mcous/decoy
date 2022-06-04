"""Errors raised by Decoy.

See the [errors guide][] for more details.

[errors guide]: ../usage/errors-and-warnings/#errors
"""
from typing import Optional, Sequence

from .spy_events import SpyEvent, VerifyRehearsal
from .stringify import count, stringify_error_message


class MissingRehearsalError(ValueError):
    """An error raised when a Decoy method is called without rehearsal(s).

    This error is raised if you use [`when`][decoy.Decoy.when],
    [`verify`][decoy.Decoy.verify], or [`prop`][decoy.Decoy.prop] incorrectly
    in your tests. When using async/await, this error can be triggered if you
    forget to include `await` with your rehearsal.

    See the [MissingRehearsalError guide][] for more details.

    [MissingRehearsalError guide]: ../usage/errors-and-warnings/#missingrehearsalerror
    """

    def __init__(self) -> None:
        super().__init__("Rehearsal not found.")


class MockNotAsyncError(TypeError):
    """An error raised when an asynchronous function is used with a synchronous mock.

    This error is raised if you pass an `async def` function
    to a synchronous stub's `then_do` method.
    See the [MockNotAsyncError guide][] for more details.

    [MockNotAsyncError guide]: ../usage/errors-and-warnings/#mocknotasyncerror
    """


class VerifyError(AssertionError):
    """An error raised when actual calls do not match rehearsals given to `verify`.

    See [spying with verify][] for more details.

    [spying with verify]: ../usage/verify/

    Attributes:
        rehearsals: Rehearsals that were being verified.
        calls: Actual calls to the mock(s).
        times: The expected number of calls to the mock, if any.
    """

    rehearsals: Sequence[VerifyRehearsal]
    calls: Sequence[SpyEvent]
    times: Optional[int]

    def __init__(
        self,
        rehearsals: Sequence[VerifyRehearsal],
        calls: Sequence[SpyEvent],
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
            include_calls=times is None or times == len(calls),
        )

        super().__init__(message)
        self.rehearsals = rehearsals
        self.calls = calls
        self.times = times
