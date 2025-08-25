"""Errors raised by Decoy.

See the [errors guide][] for more details.

[errors guide]: usage/errors-and-warnings.md#errors
"""

from typing import List, Literal

from ._internal.event import Event, EventAndState, MatchOptions
from ._internal.stringify import (
    count,
    join_lines,
    stringify_event,
    stringify_event_list,
)


class MockNameRequiredError(TypeError):
    """A name was not provided for a mock."""

    @classmethod
    def create(cls) -> "MockNameRequiredError":
        """Create the error with its message."""
        return cls("Mocks without `cls` or `func` require a `name`.")


class MockSpecInvalidError(TypeError):
    """An value passed as a mock spec is not valid."""

    @classmethod
    def create(cls, argument_name: Literal["func", "cls"]) -> "MockSpecInvalidError":
        """Create the error with its message."""
        expected_type = "funtion" if argument_name == "func" else "class"
        return cls(f"{argument_name} value must be a {expected_type}")


class ThenDoActionNotCallable(TypeError):
    """A value passed to `then_do` is not callable."""

    @classmethod
    def create(cls) -> "ThenDoActionNotCallable":
        """Create the error with its message."""
        return cls("Value passed to `then_do` must be callable.")


class MockNotAsyncError(TypeError):
    """A synchronous mock received an asynchronous function for `then_do`."""

    @classmethod
    def create(cls) -> "MockNotAsyncError":
        """Create the error with its message."""
        return cls("Synchronous mock cannot use an asynchronous callable in `then_do`.")


class NotAMockError(TypeError):
    """A Decoy method was called without a mock."""

    @classmethod
    def create(cls, method_name: str, actual_value: object) -> "NotAMockError":
        """Create the error with its message."""
        return cls(
            f"`Decoy.{method_name}` must be called with a mock, but got: {actual_value}"
        )


class SignatureMismatchError(TypeError):
    """Arguments did not match the signature of the mock."""


class VerifyError(AssertionError):
    """The actual calls to a mock did not pass the `verify` check."""

    @classmethod
    def create(
        cls,
        mock_name: str,
        match_options: MatchOptions,
        expected: Event,
        actual: List[EventAndState],
    ) -> "VerifyError":
        """Create the error with its message."""
        if match_options.times is not None:
            heading = f"Expected exactly {count(match_options.times, 'call')}:"
        else:
            heading = "Expected at least 1 call:"

        message = join_lines(
            heading,
            stringify_event(mock_name, expected),
            (f"Found {count(len(actual), 'call')}{'.' if len(actual) == 0 else ':'}"),
            stringify_event_list(mock_name, actual),
        )

        return cls(message)
