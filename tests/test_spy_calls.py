"""Tests for the spy call values."""
import pytest
from typing import List, NamedTuple

from decoy.spy_calls import SpyCall, BaseSpyRehearsal, match_call


class MatchCallSpec(NamedTuple):
    """Spec data for testing `match_call`."""

    call: SpyCall
    rehearsal: BaseSpyRehearsal
    expected_result: bool


match_call_specs: List[MatchCallSpec] = [
    MatchCallSpec(
        call=SpyCall(spy_id=42, spy_name="my_spy", args=(), kwargs={}),
        rehearsal=BaseSpyRehearsal(spy_id=42, spy_name="my_spy", args=(), kwargs={}),
        expected_result=True,
    ),
    MatchCallSpec(
        call=SpyCall(
            spy_id=42,
            spy_name="my_spy",
            args=(1, 2),
            kwargs={"foo": "bar", "baz": "qux"},
        ),
        rehearsal=BaseSpyRehearsal(
            spy_id=42,
            spy_name="my_spy",
            args=(1, 2),
            kwargs={"foo": "bar", "baz": "qux"},
        ),
        expected_result=True,
    ),
    MatchCallSpec(
        call=SpyCall(
            spy_id=42,
            spy_name="my_spy",
            args=(1, 2),
            kwargs={"foo": "bar", "baz": "qux"},
        ),
        rehearsal=BaseSpyRehearsal(
            spy_id=42,
            spy_name="my_spy",
            args=(1,),
            kwargs={"baz": "qux"},
            ignore_extra_args=True,
        ),
        expected_result=True,
    ),
    MatchCallSpec(
        call=SpyCall(spy_id=42, spy_name="my_spy", args=(), kwargs={}),
        rehearsal=BaseSpyRehearsal(spy_id=21, spy_name="my_spy", args=(), kwargs={}),
        expected_result=False,
    ),
    MatchCallSpec(
        call=SpyCall(spy_id=42, spy_name="my_spy", args=(1,), kwargs={}),
        rehearsal=BaseSpyRehearsal(spy_id=42, spy_name="my_spy", args=(), kwargs={}),
        expected_result=False,
    ),
    MatchCallSpec(
        call=SpyCall(spy_id=42, spy_name="my_spy", args=(), kwargs={}),
        rehearsal=BaseSpyRehearsal(spy_id=42, spy_name="my_spy", args=(1,), kwargs={}),
        expected_result=False,
    ),
    MatchCallSpec(
        call=SpyCall(
            spy_id=42,
            spy_name="my_spy",
            args=(1, 2),
            kwargs={"foo": "bar", "baz": "qux"},
        ),
        rehearsal=BaseSpyRehearsal(
            spy_id=42,
            spy_name="my_spy",
            args=(2,),
            kwargs={"baz": "qux"},
            ignore_extra_args=True,
        ),
        expected_result=False,
    ),
    MatchCallSpec(
        call=SpyCall(
            spy_id=42,
            spy_name="my_spy",
            args=(1, 2),
            kwargs={"foo": "bar", "baz": "qux"},
        ),
        rehearsal=BaseSpyRehearsal(
            spy_id=42,
            spy_name="my_spy",
            args=(1, 2),
            kwargs={"foo": "qux"},
            ignore_extra_args=True,
        ),
        expected_result=False,
    ),
    MatchCallSpec(
        call=SpyCall(
            spy_id=42,
            spy_name="my_spy",
            args=(1, 2),
            kwargs={"foo": "bar", "baz": "qux"},
        ),
        rehearsal=BaseSpyRehearsal(
            spy_id=42,
            spy_name="my_spy",
            args=(1, 2, 3),
            kwargs={"foo": "bar", "baz": "qux"},
            ignore_extra_args=True,
        ),
        expected_result=False,
    ),
    MatchCallSpec(
        call=SpyCall(
            spy_id=42,
            spy_name="my_spy",
            args=(1, 2),
            kwargs={"foo": "bar", "baz": "qux"},
        ),
        rehearsal=BaseSpyRehearsal(
            spy_id=42,
            spy_name="my_spy",
            args=(1, 2),
            kwargs={"foo": "bar", "baz": "qux", "fizz": "buzz"},
            ignore_extra_args=True,
        ),
        expected_result=False,
    ),
]


@pytest.mark.parametrize(MatchCallSpec._fields, match_call_specs)
def test_match_call(
    call: SpyCall,
    rehearsal: BaseSpyRehearsal,
    expected_result: bool,
) -> None:
    """It should match a call to a rehearsal."""
    result = match_call(call, rehearsal)
    assert result is expected_result
