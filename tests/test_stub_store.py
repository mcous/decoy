"""Tests for stub behavior storage."""
import pytest

from decoy.spy_events import SpyCall, SpyEvent, SpyInfo, WhenRehearsal
from decoy.stub_store import StubStore, StubBehavior


def test_get_by_call() -> None:
    """It should be able to add a StubBehavior to the store and get it back."""
    subject = StubStore()
    rehearsal = WhenRehearsal(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    behavior = StubBehavior(return_value="hello world")

    subject.add(rehearsal=rehearsal, behavior=behavior)
    result = subject.get_by_call(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="my_spy", is_async=False),
            payload=SpyCall(args=(), kwargs={}),
        )
    )

    assert result == behavior


def test_get_by_call_prefers_latest() -> None:
    """It should be prefer later stubs if multiple exist."""
    subject = StubStore()
    rehearsal_1 = WhenRehearsal(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    behavior_1 = StubBehavior(return_value="hello")
    rehearsal_2 = WhenRehearsal(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    behavior_2 = StubBehavior(return_value="goodbye")

    subject.add(rehearsal=rehearsal_1, behavior=behavior_1)
    subject.add(rehearsal=rehearsal_2, behavior=behavior_2)
    result = subject.get_by_call(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="my_spy", is_async=False),
            payload=SpyCall(args=(), kwargs={}),
        )
    )

    assert result == behavior_2


def test_get_by_call_empty() -> None:
    """It should return None if store is empty."""
    subject = StubStore()
    result = subject.get_by_call(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="my_spy", is_async=False),
            payload=SpyCall(args=(), kwargs={}),
        )
    )

    assert result is None


@pytest.mark.parametrize(
    "call",
    [
        SpyEvent(
            # spy_id does not match
            spy=SpyInfo(id=1000000000, name="my_spy", is_async=False),
            payload=SpyCall(
                args=("hello", "world"),
                kwargs={"goodbye": "so long"},
            ),
        ),
        SpyEvent(
            spy=SpyInfo(id=42, name="my_spy", is_async=False),
            # args do not match
            payload=SpyCall(
                args=("hello", "wisconsin"),
                kwargs={"goodbye": "so long"},
            ),
        ),
        SpyEvent(
            spy=SpyInfo(id=42, name="my_spy", is_async=False),
            payload=SpyCall(
                args=("hello", "wisconsin"),
                # kwargs do not match
                kwargs={"goodbye": "sofa"},
            ),
        ),
    ],
)
def test_get_by_call_no_match(call: SpyEvent) -> None:
    """It should return a no-op StubBehavior if there are no matching calls."""
    subject = StubStore()
    rehearsal = WhenRehearsal(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyCall(
            args=("hello", "world"),
            kwargs={"goodbye": "so long"},
        ),
    )
    behavior = StubBehavior(return_value="fizzbuzz")

    subject.add(rehearsal=rehearsal, behavior=behavior)

    result = subject.get_by_call(call=call)
    assert result is None


def test_get_by_call_once_behavior() -> None:
    """It should consume any behavior marked with the `once` flag."""
    subject = StubStore()
    rehearsal = WhenRehearsal(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyCall(args=(1, 2, 3), kwargs={}),
    )
    behavior = StubBehavior(return_value="fizzbuzz", once=True)

    subject.add(rehearsal=rehearsal, behavior=behavior)

    result = subject.get_by_call(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="my_spy", is_async=False),
            payload=SpyCall(args=(1, 2, 3), kwargs={}),
        )
    )

    assert result == behavior

    result = subject.get_by_call(
        call=SpyEvent(
            spy=SpyInfo(id=42, name="my_spy", is_async=False),
            payload=SpyCall(args=(1, 2, 3), kwargs={}),
        )
    )

    assert result is None


def test_clear() -> None:
    """It should consume any behavior marked with the `once` flag."""
    subject = StubStore()
    call = SpyEvent(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    rehearsal = WhenRehearsal(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    behavior = StubBehavior(return_value="fizzbuzz")

    subject.add(rehearsal=rehearsal, behavior=behavior)
    subject.clear()

    result = subject.get_by_call(call=call)

    assert result is None
