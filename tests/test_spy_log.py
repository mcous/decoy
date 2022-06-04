"""Tests for the spy call stack."""
import pytest

from decoy.errors import MissingRehearsalError
from decoy.spy_events import (
    SpyCall,
    SpyEvent,
    SpyInfo,
    SpyPropAccess,
    PropAccessType,
    WhenRehearsal,
    VerifyRehearsal,
    PropRehearsal,
)
from decoy.spy_log import SpyLog


def test_push_and_consume_when_rehearsal() -> None:
    """It should be able to push and pop from the stack."""
    subject = SpyLog()
    call = SpyEvent(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )

    subject.push(call)
    result = subject.consume_when_rehearsal(ignore_extra_args=False)

    assert isinstance(result, WhenRehearsal)
    assert call == result


def test_push_and_consume_when_rehearsal_ignore_extra_args() -> None:
    """It should be able to push and pop from the stack while ignoring extra args."""
    subject = SpyLog()
    call = SpyEvent(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )

    subject.push(call)
    result = subject.consume_when_rehearsal(ignore_extra_args=True)

    assert isinstance(result, WhenRehearsal)
    assert isinstance(result.payload, SpyCall)
    assert result.payload.ignore_extra_args is True


def test_push_and_consume_prop_rehearsal_for_when() -> None:
    """It should be able to push and consume a prop rehearsal for stubbing."""
    subject = SpyLog()
    event = SpyEvent(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyPropAccess(prop_name="my_prop", access_type=PropAccessType.GET),
    )

    subject.push(event)
    result = subject.consume_when_rehearsal(ignore_extra_args=False)
    assert isinstance(result, WhenRehearsal)
    assert result == event


def test_consume_when_rehearsal_raises_empty_error() -> None:
    """It should raise an error if the stack is empty on pop."""
    subject = SpyLog()

    with pytest.raises(MissingRehearsalError):
        subject.consume_when_rehearsal(ignore_extra_args=False)

    call = SpyEvent(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    subject.push(call)
    subject.consume_when_rehearsal(ignore_extra_args=False)

    with pytest.raises(MissingRehearsalError):
        subject.consume_when_rehearsal(ignore_extra_args=False)


def test_push_and_consume_prop_rehearsal_for_prop() -> None:
    """It should be able to push and consume a prop rehearsal for more rehearsals."""
    subject = SpyLog()
    event = SpyEvent(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyPropAccess(prop_name="my_prop", access_type=PropAccessType.GET),
    )

    subject.push(event)
    result = subject.consume_prop_rehearsal()
    assert isinstance(result, PropRehearsal)
    assert result == event


def test_consume_prop_rehearsal_raises_empty_error() -> None:
    """It should raise an error a valid rehearsal event isn't found."""
    subject = SpyLog()

    with pytest.raises(MissingRehearsalError):
        subject.consume_prop_rehearsal()

    event = SpyEvent(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyPropAccess(prop_name="my_prop", access_type=PropAccessType.GET),
    )
    subject.push(event)
    subject.consume_prop_rehearsal()

    with pytest.raises(MissingRehearsalError):
        subject.consume_prop_rehearsal()

    call = SpyEvent(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    subject.push(call)

    with pytest.raises(MissingRehearsalError):
        subject.consume_prop_rehearsal()

    event = SpyEvent(
        spy=SpyInfo(id=42, name="my_spy", is_async=False),
        payload=SpyPropAccess(prop_name="my_prop", access_type=PropAccessType.DELETE),
    )
    subject.push(event)

    with pytest.raises(MissingRehearsalError):
        subject.consume_prop_rehearsal()


def test_consume_verify_rehearsals() -> None:
    """It should be able to pop a slice off the stack, retaining order."""
    subject = SpyLog()
    call_1 = SpyEvent(
        spy=SpyInfo(id=1, name="spy_1", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    call_2 = SpyEvent(
        spy=SpyInfo(id=2, name="spy_2", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )

    subject.push(call_1)
    subject.push(call_2)

    result = subject.consume_verify_rehearsals(count=2, ignore_extra_args=False)
    assert result == [
        VerifyRehearsal(
            spy=SpyInfo(id=1, name="spy_1", is_async=False),
            payload=SpyCall(args=(), kwargs={}),
        ),
        VerifyRehearsal(
            spy=SpyInfo(id=2, name="spy_2", is_async=False),
            payload=SpyCall(args=(), kwargs={}),
        ),
    ]

    with pytest.raises(MissingRehearsalError):
        subject.consume_verify_rehearsals(count=1, ignore_extra_args=False)

    with pytest.raises(MissingRehearsalError):
        subject.consume_when_rehearsal(ignore_extra_args=False)


def test_consume_verify_rehearsals_ignore_extra_args() -> None:
    """It should be able to pop a slice off the stack, retaining order."""
    subject = SpyLog()
    call_1 = SpyEvent(
        spy=SpyInfo(id=1, name="spy_1", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    call_2 = SpyEvent(
        spy=SpyInfo(id=2, name="spy_2", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )

    subject.push(call_1)
    subject.push(call_2)

    result = subject.consume_verify_rehearsals(count=2, ignore_extra_args=True)
    assert result == [
        VerifyRehearsal(
            spy=SpyInfo(id=1, name="spy_1", is_async=False),
            payload=SpyCall(args=(), kwargs={}, ignore_extra_args=True),
        ),
        VerifyRehearsal(
            spy=SpyInfo(id=2, name="spy_2", is_async=False),
            payload=SpyCall(args=(), kwargs={}, ignore_extra_args=True),
        ),
    ]


def test_consume_verify_rehearsals_ignores_prop_gets() -> None:
    """It should be able to pop a slice off the stack, retaining order."""
    subject = SpyLog()
    call_1 = SpyEvent(
        spy=SpyInfo(id=101, name="spy_1", is_async=False),
        payload=SpyCall(args=(1,), kwargs={}),
    )
    call_2 = SpyEvent(
        spy=SpyInfo(id=101, name="spy_1", is_async=False),
        payload=SpyPropAccess(prop_name="child", access_type=PropAccessType.GET),
    )
    call_3 = SpyEvent(
        spy=SpyInfo(id=102, name="spy_1.child", is_async=False),
        payload=SpyCall(args=(2,), kwargs={}),
    )
    call_4 = SpyEvent(
        spy=SpyInfo(id=102, name="spy_1.child", is_async=False),
        payload=SpyPropAccess(prop_name="fizz", access_type=PropAccessType.DELETE),
    )
    subject.push(call_1)
    subject.push(call_2)
    subject.push(call_3)
    subject.push(call_4)

    result = subject.consume_verify_rehearsals(count=3, ignore_extra_args=False)
    assert result == [
        VerifyRehearsal(
            spy=SpyInfo(id=101, name="spy_1", is_async=False),
            payload=SpyCall(args=(1,), kwargs={}),
        ),
        VerifyRehearsal(
            spy=SpyInfo(id=102, name="spy_1.child", is_async=False),
            payload=SpyCall(args=(2,), kwargs={}),
        ),
        VerifyRehearsal(
            spy=SpyInfo(id=102, name="spy_1.child", is_async=False),
            payload=SpyPropAccess(prop_name="fizz", access_type=PropAccessType.DELETE),
        ),
    ]


def test_consume_verify_rehearsals_raises_error() -> None:
    """It should raise an error if the stack has too few members to pop a slice."""
    subject = SpyLog()
    call_1 = SpyEvent(
        spy=SpyInfo(id=1, name="spy_1", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )

    subject.push(call_1)

    with pytest.raises(MissingRehearsalError):
        subject.consume_verify_rehearsals(count=2, ignore_extra_args=False)


def test_get_calls_to_verify() -> None:
    """It can get a list of calls made matching spy IDs of given rehearsals."""
    subject = SpyLog()
    call_1 = SpyEvent(
        spy=SpyInfo(id=101, name="spy_1", is_async=False),
        payload=SpyCall(args=(1,), kwargs={}),
    )
    call_2 = SpyEvent(
        spy=SpyInfo(id=101, name="spy_1", is_async=False),
        payload=SpyCall(args=(2,), kwargs={}),
    )
    call_3 = SpyEvent(
        spy=SpyInfo(id=202, name="spy_2", is_async=False),
        payload=SpyCall(args=(1,), kwargs={}),
    )
    call_4 = SpyEvent(
        spy=SpyInfo(id=101, name="spy_1", is_async=False),
        payload=SpyCall(args=(1,), kwargs={}),
    )

    subject.push(call_1)
    subject.push(call_2)
    subject.consume_when_rehearsal(ignore_extra_args=False)
    subject.push(call_3)
    subject.push(call_4)

    result = subject.get_calls_to_verify([101])
    assert result == [call_1, call_4]

    result = subject.get_calls_to_verify([101, 202])
    assert result == [call_1, call_3, call_4]

    result = subject.get_calls_to_verify([303])
    assert result == []


def test_get_calls_to_verify_skips_prop_gets() -> None:
    """It does not return prop getters for verification."""
    subject = SpyLog()

    call_1 = SpyEvent(
        spy=SpyInfo(id=101, name="spy_1", is_async=False),
        payload=SpyPropAccess(prop_name="child", access_type=PropAccessType.GET),
    )
    call_2 = PropRehearsal(
        spy=SpyInfo(id=101, name="spy_1", is_async=False),
        payload=SpyPropAccess(prop_name="child", access_type=PropAccessType.GET),
    )
    call_3 = SpyEvent(
        spy=SpyInfo(id=102, name="spy_1.child", is_async=False),
        payload=SpyCall(args=(2,), kwargs={}),
    )
    call_4 = SpyEvent(
        spy=SpyInfo(id=102, name="spy_1.child", is_async=False),
        payload=SpyPropAccess(prop_name="fizz", access_type=PropAccessType.DELETE),
    )

    subject.push(call_1)
    subject.push(call_2)
    subject.push(call_3)
    subject.push(call_4)
    result = subject.get_calls_to_verify([101, 102])
    assert result == [call_3, call_4]


def test_get_all() -> None:
    """It can get a list of all calls and rehearsals."""
    subject = SpyLog()
    call_1 = SpyEvent(
        spy=SpyInfo(id=101, name="spy_1", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    call_2 = SpyEvent(
        spy=SpyInfo(id=101, name="spy_1", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    call_3 = SpyEvent(
        spy=SpyInfo(id=202, name="spy_2", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )

    subject.push(call_1)
    subject.consume_when_rehearsal(ignore_extra_args=False)
    subject.push(call_2)
    subject.push(call_3)
    subject.consume_when_rehearsal(ignore_extra_args=False)

    assert subject.get_all() == [
        WhenRehearsal(
            spy=SpyInfo(id=101, name="spy_1", is_async=False),
            payload=SpyCall(args=(), kwargs={}),
        ),
        SpyEvent(
            spy=SpyInfo(id=101, name="spy_1", is_async=False),
            payload=SpyCall(args=(), kwargs={}),
        ),
        SpyEvent(
            spy=SpyInfo(id=202, name="spy_2", is_async=False),
            payload=SpyCall(args=(), kwargs={}),
        ),
    ]


def test_clear() -> None:
    """It can clear all calls and rehearsals."""
    subject = SpyLog()
    call_1 = SpyEvent(
        spy=SpyInfo(id=101, name="spy_1", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    call_2 = SpyEvent(
        spy=SpyInfo(id=101, name="spy_1", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    call_3 = SpyEvent(
        spy=SpyInfo(id=202, name="spy_2", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )

    subject.push(call_1)
    subject.consume_when_rehearsal(ignore_extra_args=False)
    subject.push(call_2)
    subject.push(call_3)
    subject.consume_when_rehearsal(ignore_extra_args=False)
    subject.clear()

    assert subject.get_all() == []
