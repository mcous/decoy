"""Tests for the spy interaction event values."""
import pytest
from typing import List, NamedTuple

from decoy.spy_events import (
    SpyCall,
    SpyEvent,
    SpyRehearsal,
    WhenRehearsal,
    VerifyRehearsal,
    match_event,
)


class MatchEventSpec(NamedTuple):
    """Spec data for testing `match_event`."""

    event: SpyEvent
    rehearsal: SpyRehearsal
    expected_result: bool


match_event_specs: List[MatchEventSpec] = [
    MatchEventSpec(
        event=SpyEvent(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(), kwargs={}),
        ),
        rehearsal=WhenRehearsal(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(), kwargs={}),
        ),
        expected_result=True,
    ),
    MatchEventSpec(
        event=SpyEvent(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(1, 2), kwargs={"foo": "bar", "baz": "qux"}),
        ),
        rehearsal=VerifyRehearsal(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(1, 2), kwargs={"foo": "bar", "baz": "qux"}),
        ),
        expected_result=True,
    ),
    MatchEventSpec(
        event=SpyEvent(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(1, 2), kwargs={"foo": "bar", "baz": "qux"}),
        ),
        rehearsal=WhenRehearsal(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(1,), kwargs={"baz": "qux"}, ignore_extra_args=True),
        ),
        expected_result=True,
    ),
    MatchEventSpec(
        event=SpyEvent(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(), kwargs={}),
        ),
        rehearsal=VerifyRehearsal(
            spy_id=21,
            spy_name="my_spy",
            payload=SpyCall(args=(), kwargs={}),
        ),
        expected_result=False,
    ),
    MatchEventSpec(
        event=SpyEvent(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(1,), kwargs={}),
        ),
        rehearsal=WhenRehearsal(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(), kwargs={}),
        ),
        expected_result=False,
    ),
    MatchEventSpec(
        event=SpyEvent(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(), kwargs={}),
        ),
        rehearsal=VerifyRehearsal(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(1,), kwargs={}),
        ),
        expected_result=False,
    ),
    MatchEventSpec(
        event=SpyEvent(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(1, 2), kwargs={"foo": "bar", "baz": "qux"}),
        ),
        rehearsal=WhenRehearsal(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(2,), kwargs={"baz": "qux"}, ignore_extra_args=True),
        ),
        expected_result=False,
    ),
    MatchEventSpec(
        event=SpyEvent(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(1, 2), kwargs={"foo": "bar", "baz": "qux"}),
        ),
        rehearsal=VerifyRehearsal(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(1, 2), kwargs={"foo": "qux"}, ignore_extra_args=True),
        ),
        expected_result=False,
    ),
    MatchEventSpec(
        event=SpyEvent(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(1, 2), kwargs={"foo": "bar", "baz": "qux"}),
        ),
        rehearsal=WhenRehearsal(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(
                args=(1, 2, 3),
                kwargs={"foo": "bar", "baz": "qux"},
                ignore_extra_args=True,
            ),
        ),
        expected_result=False,
    ),
    MatchEventSpec(
        event=SpyEvent(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(args=(1, 2), kwargs={"foo": "bar", "baz": "qux"}),
        ),
        rehearsal=VerifyRehearsal(
            spy_id=42,
            spy_name="my_spy",
            payload=SpyCall(
                args=(1, 2),
                kwargs={"foo": "bar", "baz": "qux", "fizz": "buzz"},
                ignore_extra_args=True,
            ),
        ),
        expected_result=False,
    ),
]


@pytest.mark.parametrize(MatchEventSpec._fields, match_event_specs)
def test_match_event(
    event: SpyEvent,
    rehearsal: SpyRehearsal,
    expected_result: bool,
) -> None:
    """It should match a call to a rehearsal."""
    result = match_event(event, rehearsal)
    assert result is expected_result
