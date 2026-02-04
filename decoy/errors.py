"""Errors raised by Decoy.

See the [errors guide][] for more details.

[errors guide]: usage/errors-and-warnings.md#errors
"""

from typing import Optional, Sequence

from .spy_events import SpyEvent, VerifyRehearsal
from .stringify import count, stringify_error_message


class MockNameRequiredError(ValueError):
    """A name was not provided for a mock."""

    @classmethod
    def create(cls) -> "MockNameRequiredError":
        """Create a MockNameRequiredError."""
        return cls("Mocks without `cls` or `func` require a `name`.")


class MockSpecInvalidError(TypeError):
    """A value passed as a mock spec is not valid."""


class MissingRehearsalError(ValueError):
    """A Decoy method was called without rehearsal(s).

    This error is raised if you use [`when`][decoy.Decoy.when],
    [`verify`][decoy.Decoy.verify], or [`prop`][decoy.Decoy.prop] incorrectly
    in your tests. When using async/await, this error can be triggered if you
    forget to include `await` with your rehearsal.
    """

    @classmethod
    def create(cls) -> "MissingRehearsalError":
        """Create a MissingRehearsalError."""
        return cls("Rehearsal not found.")


class NotAMockError(TypeError):
    """A Decoy method was called without a mock."""


class ThenDoActionNotCallableError(TypeError):
    """A value passed to `then_do` is not callable."""


class MockNotAsyncError(TypeError):
    """An asynchronous function was passed to a synchronous mock.

    This error is raised if you pass an `async def` function
    to a synchronous stub's [`then_do`][decoy.Stub.then_do] method.
    """


class SignatureMismatchError(TypeError):
    """Arguments did not match the signature of the mock."""


class VerifyError(AssertionError):
    """A [`Decoy.verify`][decoy.Decoy.verify] assertion failed."""

    rehearsals: Sequence[VerifyRehearsal]
    calls: Sequence[SpyEvent]
    times: Optional[int]

    @classmethod
    def create(
        cls,
        rehearsals: Sequence[VerifyRehearsal],
        calls: Sequence[SpyEvent],
        times: Optional[int],
    ) -> "VerifyError":
        """Create a VerifyError."""
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

        result = cls(message)
        result.rehearsals = rehearsals
        result.calls = calls
        result.times = times

        return result


class VerifyOrderError(VerifyError):
    """A [`Decoy.verify_order`][decoy.next.Decoy.verify_order] assertion failed."""


class NoMatcherValueCapturedError(ValueError):
    """An error raised if a [decoy.next.Matcher][] has not captured any matching values."""
