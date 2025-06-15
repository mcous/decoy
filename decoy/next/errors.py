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


class MockNameRequiredError(ValueError):
    """A name was not provided for a mock."""

    def __init__(self) -> None:
        super().__init__("Mocks without `cls` or `func` require a `name`.")


class MockSpecInvalidError(ValueError):
    """An value passed as a mock spec is not valid."""

    def __init__(self, argument_name: Literal["func", "cls"]) -> None:
        expected_type = "funtion" if argument_name == "func" else "class"
        super().__init__(f"{argument_name} value must be a {expected_type}")


class ThenDoActionNotCallable(ValueError):
    """A value passed to `then_do` is not callable."""

    def __init__(self) -> None:
        super().__init__("Value passed to `then_do` must be callable.")


class MockNotAsyncError(TypeError):
    """A synchronous mock received an asynchronous function for `then_do`."""

    def __init__(self) -> None:
        super().__init__(
            "Synchronous mock cannot use an asynchronous callable in `then_do`."
        )


class NotAMockError(TypeError):
    """A Decoy method was called without a mock."""


class VerifyError(AssertionError):
    """The actual calls to a mock did not pass the `verify` check."""

    def __init__(
        self,
        mock_name: str,
        match_options: MatchOptions,
        expected: Event,
        actual: List[EventAndState],
    ) -> None:
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

        super().__init__(message)
