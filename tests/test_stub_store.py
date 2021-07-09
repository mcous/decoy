"""Tests for stub behavior storage."""
import pytest

from decoy.spy import SpyCall, SpyRehearsal
from decoy.stub_store import StubStore, StubBehavior


def test_get_by_call() -> None:
    """It should be able to add a StubBehavior to the store and get it back."""
    subject = StubStore()
    rehearsal = SpyRehearsal(spy_id=42, spy_name="my_spy", args=(), kwargs={})
    behavior = StubBehavior(return_value="hello world")

    subject.add(rehearsal=rehearsal, behavior=behavior)
    result = subject.get_by_call(
        call=SpyCall(spy_id=42, spy_name="my_spy", args=(), kwargs={})
    )

    assert result == behavior


def test_get_by_call_prefers_latest() -> None:
    """It should be prefer later stubs if multiple exist."""
    subject = StubStore()
    rehearsal_1 = SpyRehearsal(spy_id=42, spy_name="my_spy", args=(), kwargs={})
    behavior_1 = StubBehavior(return_value="hello")
    rehearsal_2 = SpyRehearsal(spy_id=42, spy_name="my_spy", args=(), kwargs={})
    behavior_2 = StubBehavior(return_value="goodbye")

    subject.add(rehearsal=rehearsal_1, behavior=behavior_1)
    subject.add(rehearsal=rehearsal_2, behavior=behavior_2)
    result = subject.get_by_call(
        call=SpyCall(spy_id=42, spy_name="my_spy", args=(), kwargs={})
    )

    assert result == behavior_2


def test_get_by_call_empty() -> None:
    """It should return a no-op StubBehavior if store is empty."""
    subject = StubStore()
    result = subject.get_by_call(
        call=SpyCall(spy_id=42, spy_name="my_spy", args=(), kwargs={})
    )

    assert result == StubBehavior()


@pytest.mark.parametrize(
    "call",
    [
        SpyCall(
            # spy_id does not match
            spy_id=24,
            spy_name="my_spy",
            args=("hello", "world"),
            kwargs={"goodbye": "so long"},
        ),
        SpyCall(
            spy_id=42,
            spy_name="my_spy",
            # args do not match
            args=("hello", "wisconsin"),
            kwargs={"goodbye": "so long"},
        ),
        SpyCall(
            spy_id=42,
            spy_name="my_spy",
            args=("hello", "wisconsin"),
            # kwargs do not match
            kwargs={"goodbye": "sofa"},
        ),
    ],
)
def test_get_by_call_no_match(call: SpyCall) -> None:
    """It should return a no-op StubBehavior if there are no matching calls."""
    subject = StubStore()
    rehearsal = SpyRehearsal(
        spy_id=42,
        spy_name="my_spy",
        args=("hello", "world"),
        kwargs={"goodbye": "so long"},
    )
    behavior = StubBehavior(return_value="fizzbuzz")

    subject.add(rehearsal=rehearsal, behavior=behavior)

    result = subject.get_by_call(call=call)
    assert result == StubBehavior()


def test_get_by_call_once_behavior() -> None:
    """It should consume any behavior marked with the `once` flag."""
    subject = StubStore()
    rehearsal = SpyRehearsal(spy_id=42, spy_name="my_spy", args=(1, 2, 3), kwargs={})
    behavior = StubBehavior(return_value="fizzbuzz", once=True)

    subject.add(rehearsal=rehearsal, behavior=behavior)

    result = subject.get_by_call(
        call=SpyCall(spy_id=42, spy_name="my_spy", args=(1, 2, 3), kwargs={})
    )

    assert result == behavior

    result = subject.get_by_call(
        call=SpyCall(spy_id=42, spy_name="my_spy", args=(1, 2, 3), kwargs={})
    )

    assert result == StubBehavior()


def test_clear() -> None:
    """It should consume any behavior marked with the `once` flag."""
    subject = StubStore()
    rehearsal = SpyRehearsal(spy_id=42, spy_name="my_spy", args=(), kwargs={})
    behavior = StubBehavior(return_value="fizzbuzz")

    subject.add(rehearsal=rehearsal, behavior=behavior)
    subject.clear()

    result = subject.get_by_call(call=rehearsal)

    assert result == StubBehavior()
