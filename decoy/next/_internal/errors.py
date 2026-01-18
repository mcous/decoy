from typing import Literal

from ... import errors
from .stringify import (
    count,
    join_lines,
    stringify_event,
    stringify_event_entry_list,
    stringify_event_list,
    stringify_verification_list,
)
from .values import Event, EventEntry, MatchOptions, VerificationEntry


def createMockNameRequiredError() -> errors.MockNameRequiredError:
    """Create a MockNameRequiredError."""
    return errors.MockNameRequiredError(
        "Mocks without `cls` or `func` require a `name`."
    )


def createMockSpecInvalidError(
    argument_name: Literal["func", "cls"],
) -> errors.MockSpecInvalidError:
    """Create a MockSpecInvalidError."""
    expected_type = "function" if argument_name == "func" else "class"

    return errors.MockSpecInvalidError(
        f"{argument_name} value must be a {expected_type}"
    )


def createNotAMockError(method_name: str, actual_value: object) -> errors.NotAMockError:
    """Create a NotAMockError."""
    return errors.NotAMockError(
        f"`Decoy.{method_name}` must be called with a mock, but got: {actual_value}"
    )


def createThenDoActionNotCallableError() -> errors.ThenDoActionNotCallableError:
    """Create a ThenDoActionNotCallableError."""
    return errors.ThenDoActionNotCallableError(
        "Value passed to `then_do` must be callable."
    )


def createMockNotAsyncError() -> errors.MockNotAsyncError:
    """Create a MockNotAsyncError."""
    return errors.MockNotAsyncError(
        "Synchronous mock cannot use an asynchronous callable in `then_do`."
    )


def createSignatureMismatchError(
    source: TypeError | ValueError,
) -> errors.SignatureMismatchError:
    """Create a SignatureMismatchError."""
    return errors.SignatureMismatchError(source)


def createVerifyError(
    mock_name: str,
    match_options: MatchOptions,
    expected: Event,
    all_events: list[EventEntry],
) -> errors.VerifyError:
    """Create a VerifyError."""
    if match_options.times is not None:
        heading = f"Expected exactly {count(match_options.times, 'call')}:"
    else:
        heading = "Expected at least 1 call:"

    message = join_lines(
        heading,
        f"1.\t{stringify_event(mock_name, expected)}",
        (
            f"Found {count(len(all_events), 'call')}{'.' if len(all_events) == 0 else ':'}"
        ),
        stringify_event_list(mock_name, [entry.event for entry in all_events]),
    )

    return errors.VerifyError(message)


def createVerifyOrderError(
    verifications: list[VerificationEntry],
    all_events: list[EventEntry],
) -> errors.VerifyOrderError:
    """Create a VerifyOrderError."""
    message = join_lines(
        "Expected call sequence:",
        stringify_verification_list(verifications),
        f"Found {len(all_events)} calls:",
        stringify_event_entry_list(all_events),
    )

    return errors.VerifyOrderError(message)
