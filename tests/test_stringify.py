"""Tests for stringification utilities."""
import pytest
from typing import NamedTuple

from decoy.spy_events import SpyCall, SpyEvent, SpyInfo, SpyPropAccess, PropAccessType
from decoy.stringify import stringify_call


class StringifyCallSpec(NamedTuple):
    """Spec data for stringify_call tests."""

    call: SpyEvent
    expected: str


stringify_call_specs = [
    StringifyCallSpec(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="some.name"),
            payload=SpyCall(args=(), kwargs={}),
        ),
        expected="some.name()",
    ),
    StringifyCallSpec(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="some.name"),
            payload=SpyCall(args=(1,), kwargs={}),
        ),
        expected="some.name(1)",
    ),
    StringifyCallSpec(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="some.name"),
            payload=SpyCall(args=(1, "2"), kwargs={}),
        ),
        expected="some.name(1, '2')",
    ),
    StringifyCallSpec(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="some.name"),
            payload=SpyCall(args=(), kwargs={"foo": "bar"}),
        ),
        expected="some.name(foo='bar')",
    ),
    StringifyCallSpec(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="some.name"),
            payload=SpyCall(
                args=(1, 2),
                kwargs={"foo": "bar", "baz": False},
            ),
        ),
        expected="some.name(1, 2, foo='bar', baz=False)",
    ),
    StringifyCallSpec(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="some.name"),
            payload=SpyCall(
                args=(),
                kwargs={},
                ignore_extra_args=True,
            ),
        ),
        expected="some.name() - ignoring unspecified arguments",
    ),
    StringifyCallSpec(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="some"),
            payload=SpyPropAccess(prop_name="name", access_type=PropAccessType.GET),
        ),
        expected="some.name",
    ),
    StringifyCallSpec(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="some"),
            payload=SpyPropAccess(
                prop_name="name",
                access_type=PropAccessType.SET,
                value=42,
            ),
        ),
        expected="some.name = 42",
    ),
    StringifyCallSpec(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="some"),
            payload=SpyPropAccess(prop_name="name", access_type=PropAccessType.DELETE),
        ),
        expected="del some.name",
    ),
]


@pytest.mark.parametrize(StringifyCallSpec._fields, stringify_call_specs)
def test_spy_call_stringifies(call: SpyEvent, expected: str) -> None:
    """It should serialize SpyEvents to strings."""
    assert stringify_call(call) == expected
