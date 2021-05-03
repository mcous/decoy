"""Tests for warning messages."""
from os import linesep

from decoy.spy import SpyCall
from decoy.stub import Stub
from decoy.warnings import MissingStubWarning


def test_no_stubbing_found_warning() -> None:
    """It should print a helpful error message if a call misses a stub."""
    call = SpyCall(spy_id="123", spy_name="spy", args=(1, 2), kwargs={"foo": "bar"})
    stub = Stub(
        rehearsal=SpyCall(
            spy_id="123",
            spy_name="spy",
            args=(3, 4),
            kwargs={"baz": "qux"},
        )
    )

    result = MissingStubWarning(call=call, stubs=[stub])

    assert str(result) == (
        f"Stub was called but no matching rehearsal found.{linesep}"
        f"Found 1 rehearsal:{linesep}"
        f"1.\tspy(3, 4, baz='qux'){linesep}"
        f"Actual call:{linesep}"
        "\tspy(1, 2, foo='bar')"
    )


def test_no_stubbing_found_warning_plural() -> None:
    """It should print a helpful message if a call misses multiple stubs."""
    call = SpyCall(spy_id="123", spy_name="spy", args=(1, 2), kwargs={"foo": "bar"})
    stubs = [
        Stub(
            rehearsal=SpyCall(
                spy_id="123",
                spy_name="spy",
                args=(3, 4),
                kwargs={"baz": "qux"},
            )
        ),
        Stub(
            rehearsal=SpyCall(
                spy_id="123",
                spy_name="spy",
                args=(5, 6),
                kwargs={"fizz": "buzz"},
            )
        ),
    ]

    result = MissingStubWarning(call=call, stubs=stubs)

    assert str(result) == (
        f"Stub was called but no matching rehearsal found.{linesep}"
        f"Found 2 rehearsals:{linesep}"
        f"1.\tspy(3, 4, baz='qux'){linesep}"
        f"2.\tspy(5, 6, fizz='buzz'){linesep}"
        f"Actual call:{linesep}"
        "\tspy(1, 2, foo='bar')"
    )
