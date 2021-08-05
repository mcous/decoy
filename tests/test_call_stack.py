"""Tests for the spy call stack."""
import pytest

from decoy.errors import MissingRehearsalError
from decoy.spy_calls import SpyCall, WhenRehearsal, VerifyRehearsal
from decoy.call_stack import CallStack


def test_push_and_consume_when_rehearsal() -> None:
    """It should be able to push and pop from the stack."""
    subject = CallStack()
    call = SpyCall(spy_id=42, spy_name="my_spy", args=(), kwargs={})

    subject.push(call)
    result = subject.consume_when_rehearsal()

    assert isinstance(result, WhenRehearsal)
    assert call == result


def test_consume_when_rehearsal_raises_empty_error() -> None:
    """It should raise an error if the stack is empty on pop."""
    subject = CallStack()

    with pytest.raises(MissingRehearsalError):
        subject.consume_when_rehearsal()

    call = SpyCall(spy_id=42, spy_name="my_spy", args=(), kwargs={})
    subject.push(call)
    subject.consume_when_rehearsal()

    with pytest.raises(MissingRehearsalError):
        subject.consume_when_rehearsal()


def test_consume_verify_rehearsals() -> None:
    """It should be able to pop a slice off the stack, retaining order."""
    subject = CallStack()
    call_1 = SpyCall(spy_id=1, spy_name="spy_1", args=(), kwargs={})
    call_2 = SpyCall(spy_id=2, spy_name="spy_2", args=(), kwargs={})

    subject.push(call_1)
    subject.push(call_2)

    result = subject.consume_verify_rehearsals(count=2)
    assert result == [
        VerifyRehearsal(spy_id=1, spy_name="spy_1", args=(), kwargs={}),
        VerifyRehearsal(spy_id=2, spy_name="spy_2", args=(), kwargs={}),
    ]

    with pytest.raises(MissingRehearsalError):
        subject.consume_verify_rehearsals(count=1)

    with pytest.raises(MissingRehearsalError):
        subject.consume_when_rehearsal()


def test_consume_verify_rehearsals_raises_error() -> None:
    """It should raise an error if the stack has too few members to pop a slice."""
    subject = CallStack()
    call_1 = SpyCall(spy_id=1, spy_name="spy_1", args=(), kwargs={})

    subject.push(call_1)

    with pytest.raises(MissingRehearsalError):
        subject.consume_verify_rehearsals(count=2)


def test_get_by_rehearsal() -> None:
    """It can get a list of calls made matching spy IDs of given rehearsals."""
    subject = CallStack()
    call_1 = SpyCall(spy_id=101, spy_name="spy_1", args=(1,), kwargs={})
    call_2 = SpyCall(spy_id=101, spy_name="spy_1", args=(2,), kwargs={})
    call_3 = SpyCall(spy_id=202, spy_name="spy_2", args=(1,), kwargs={})
    call_4 = SpyCall(spy_id=101, spy_name="spy_1", args=(1,), kwargs={})

    subject.push(call_1)
    subject.push(call_2)
    subject.consume_when_rehearsal()
    subject.push(call_3)
    subject.push(call_4)

    result = subject.get_by_rehearsals(
        [VerifyRehearsal(spy_id=101, spy_name="spy_1", args=(1,), kwargs={})]
    )
    assert result == [call_1, call_4]

    result = subject.get_by_rehearsals(
        [
            VerifyRehearsal(spy_id=101, spy_name="spy_1", args=(2,), kwargs={}),
            VerifyRehearsal(spy_id=202, spy_name="spy_2", args=(1,), kwargs={}),
        ]
    )
    assert result == [call_1, call_3, call_4]

    result = subject.get_by_rehearsals(
        [VerifyRehearsal(spy_id=303, spy_name="spy_3", args=(1,), kwargs={})]
    )
    assert result == []


def test_get_all() -> None:
    """It can get a list of all calls and rehearsals."""
    subject = CallStack()
    call_1 = SpyCall(spy_id=101, spy_name="spy_1", args=(), kwargs={})
    call_2 = SpyCall(spy_id=101, spy_name="spy_1", args=(), kwargs={})
    call_3 = SpyCall(spy_id=202, spy_name="spy_2", args=(), kwargs={})

    subject.push(call_1)
    subject.consume_when_rehearsal()
    subject.push(call_2)
    subject.push(call_3)
    subject.consume_when_rehearsal()

    assert subject.get_all() == [
        WhenRehearsal(spy_id=101, spy_name="spy_1", args=(), kwargs={}),
        SpyCall(spy_id=101, spy_name="spy_1", args=(), kwargs={}),
        WhenRehearsal(spy_id=202, spy_name="spy_2", args=(), kwargs={}),
    ]


def test_clear() -> None:
    """It can clear all calls and rehearsals."""
    subject = CallStack()
    call_1 = SpyCall(spy_id=101, spy_name="spy_1", args=(), kwargs={})
    call_2 = SpyCall(spy_id=101, spy_name="spy_1", args=(), kwargs={})
    call_3 = SpyCall(spy_id=202, spy_name="spy_2", args=(), kwargs={})

    subject.push(call_1)
    subject.consume_when_rehearsal()
    subject.push(call_2)
    subject.push(call_3)
    subject.consume_when_rehearsal()
    subject.clear()

    assert subject.get_all() == []
