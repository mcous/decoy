"""Tests for the spy call stack."""
import pytest

from decoy.errors import MissingRehearsalError
from decoy.spy import SpyCall, SpyRehearsal
from decoy.call_stack import CallStack


def test_push_and_consume() -> None:
    """It should be able to push and pop from the stack."""
    subject = CallStack()
    call = SpyCall(spy_id=42, spy_name="my_spy", args=(), kwargs={})

    subject.push(call)
    result = subject.consume_rehearsal()

    assert isinstance(result, SpyRehearsal)
    assert result.spy_id == call.spy_id
    assert result.spy_name == call.spy_name
    assert result.args == call.args
    assert result.kwargs == call.kwargs


def test_pop_raises_empty_error() -> None:
    """It should raise an error if the stack is empty on pop."""
    subject = CallStack()
    call = SpyCall(spy_id=42, spy_name="my_spy", args=(), kwargs={})

    subject.push(call)
    subject.consume_rehearsal()

    with pytest.raises(MissingRehearsalError):
        subject.consume_rehearsal()


def test_pop_slice() -> None:
    """It should be able to pop a slice off the stack, retaining order."""
    subject = CallStack()
    call_1 = SpyCall(spy_id=1, spy_name="spy_1", args=(), kwargs={})
    call_2 = SpyCall(spy_id=2, spy_name="spy_2", args=(), kwargs={})

    subject.push(call_1)
    subject.push(call_2)

    result = subject.consume_rehearsals(count=2)
    assert result == [
        SpyRehearsal(spy_id=1, spy_name="spy_1", args=(), kwargs={}),
        SpyRehearsal(spy_id=2, spy_name="spy_2", args=(), kwargs={}),
    ]

    with pytest.raises(MissingRehearsalError):
        subject.consume_rehearsal()


def test_pop_slice_raises_error() -> None:
    """It should raise an error if the stack has too few members to pop a slice."""
    subject = CallStack()
    call_1 = SpyCall(spy_id=1, spy_name="spy_1", args=(), kwargs={})

    subject.push(call_1)

    with pytest.raises(MissingRehearsalError):
        subject.consume_rehearsals(count=2)


def test_get_by_rehearsal() -> None:
    """It can get a list of calls made matching a given rehearsal."""
    subject = CallStack()
    call_1 = SpyCall(spy_id=101, spy_name="spy_1", args=(1,), kwargs={})
    call_2 = SpyCall(spy_id=101, spy_name="spy_1", args=(2,), kwargs={})
    call_3 = SpyCall(spy_id=202, spy_name="spy_2", args=(1,), kwargs={})
    call_4 = SpyCall(spy_id=101, spy_name="spy_1", args=(1,), kwargs={})

    subject.push(call_1)
    subject.push(call_2)
    subject.consume_rehearsal()
    subject.push(call_3)
    subject.push(call_4)

    result = subject.get_by_rehearsals(
        [SpyRehearsal(spy_id=101, spy_name="spy_1", args=(1,), kwargs={})]
    )
    assert result == [call_1, call_4]

    result = subject.get_by_rehearsals(
        [
            SpyRehearsal(spy_id=101, spy_name="spy_1", args=(2,), kwargs={}),
            SpyRehearsal(spy_id=202, spy_name="spy_2", args=(1,), kwargs={}),
        ]
    )
    assert result == [call_3]

    result = subject.get_by_rehearsals(
        [SpyRehearsal(spy_id=303, spy_name="spy_3", args=(1,), kwargs={})]
    )
    assert result == []


def test_get_all() -> None:
    """It can get a list of all calls and rehearsals."""
    subject = CallStack()
    call_1 = SpyCall(spy_id=101, spy_name="spy_1", args=(), kwargs={})
    call_2 = SpyCall(spy_id=101, spy_name="spy_1", args=(), kwargs={})
    call_3 = SpyCall(spy_id=202, spy_name="spy_2", args=(), kwargs={})

    subject.push(call_1)
    subject.consume_rehearsal()
    subject.push(call_2)
    subject.push(call_3)
    subject.consume_rehearsal()

    assert subject.get_all() == [
        SpyRehearsal(spy_id=101, spy_name="spy_1", args=(), kwargs={}),
        SpyCall(spy_id=101, spy_name="spy_1", args=(), kwargs={}),
        SpyRehearsal(spy_id=202, spy_name="spy_2", args=(), kwargs={}),
    ]


def test_clear() -> None:
    """It can clear all calls and rehearsals."""
    subject = CallStack()
    call_1 = SpyCall(spy_id=101, spy_name="spy_1", args=(), kwargs={})
    call_2 = SpyCall(spy_id=101, spy_name="spy_1", args=(), kwargs={})
    call_3 = SpyCall(spy_id=202, spy_name="spy_2", args=(), kwargs={})

    subject.push(call_1)
    subject.consume_rehearsal()
    subject.push(call_2)
    subject.push(call_3)
    subject.consume_rehearsal()
    subject.clear()

    assert subject.get_all() == []
