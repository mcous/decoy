"""Tests for stringification utilities."""
import pytest
from typing import NamedTuple

from decoy.spy_calls import SpyCall
from decoy.stringify import stringify_call


class StringifyCallSpec(NamedTuple):
    """Spec data for stringify_call tests."""

    call: SpyCall
    expected: str


stringify_call_specs = [
    StringifyCallSpec(
        call=SpyCall(spy_id=42, spy_name="some.name", args=(), kwargs={}),
        expected="some.name()",
    ),
    StringifyCallSpec(
        call=SpyCall(spy_id=42, spy_name="some.name", args=(1,), kwargs={}),
        expected="some.name(1)",
    ),
    StringifyCallSpec(
        call=SpyCall(spy_id=42, spy_name="some.name", args=(1, "2"), kwargs={}),
        expected="some.name(1, '2')",
    ),
    StringifyCallSpec(
        call=SpyCall(spy_id=42, spy_name="some.name", args=(), kwargs={"foo": "bar"}),
        expected="some.name(foo='bar')",
    ),
    StringifyCallSpec(
        call=SpyCall(
            spy_id=42,
            spy_name="some.name",
            args=(1, 2),
            kwargs={"foo": "bar", "baz": False},
        ),
        expected="some.name(1, 2, foo='bar', baz=False)",
    ),
    StringifyCallSpec(
        call=SpyCall(
            spy_id=42, spy_name="some.name", args=(), kwargs={}, ignore_extra_args=True
        ),
        expected="some.name() - ignoring unspecified arguments",
    ),
]


@pytest.mark.parametrize(StringifyCallSpec._fields, stringify_call_specs)
def test_spy_call_stringifies(call: SpyCall, expected: str) -> None:
    """It should serialize SpyCalls to strings."""
    assert stringify_call(call) == expected
