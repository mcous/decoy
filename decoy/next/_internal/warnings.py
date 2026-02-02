from ... import warnings
from .stringify import count, join_lines, stringify_event, stringify_event_list
from .values import CallEvent, Event


def createMiscalledStubWarning(
    name: str,
    expected_events: list[Event],
    actual_event: CallEvent,
) -> warnings.MiscalledStubWarning:
    """Create a MiscalledStubWarning."""
    message = join_lines(
        "Stub was called but no matching rehearsal found.",
        f"Found {count(len(expected_events), 'rehearsal')}:",
        stringify_event_list(name, expected_events),
        "Found 1 call:",
        f"1.\t{stringify_event(name, actual_event)}",
    )

    return warnings.MiscalledStubWarning(message)


def createRedundantVerifyWarning(
    name: str,
    event: Event,
) -> warnings.RedundantVerifyWarning:
    """Create a RedundantVerifyWarning."""
    message = join_lines(
        "The same rehearsal was used in both a `when` and a `verify`.",
        "This is redundant and probably a misuse of the mock.",
        f"\t{stringify_event(name, event)}",
        "See https://michael.cousins.io/decoy/usage/errors-and-warnings/#redundantverifywarning",
    )

    return warnings.RedundantVerifyWarning(message)
