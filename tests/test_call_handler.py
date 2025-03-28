"""Tests for the SpyEvent handling."""

import pytest

from decoy import Decoy
from decoy.call_handler import CallHandler, CallHandlerResult
from decoy.spy_log import SpyLog
from decoy.spy_events import SpyInfo, SpyCall, SpyEvent, SpyPropAccess, PropAccessType
from decoy.stub_store import StubBehavior, StubStore


@pytest.fixture()
def spy_log(decoy: Decoy) -> SpyLog:
    """Get a mock instance of a SpyLog."""
    return decoy.mock(cls=SpyLog)


@pytest.fixture()
def stub_store(decoy: Decoy) -> StubStore:
    """Get a mock instance of a StubStore."""
    return decoy.mock(cls=StubStore)


@pytest.fixture()
def subject(spy_log: SpyLog, stub_store: StubStore) -> CallHandler:
    """Get a CallHandler instance with its dependencies mocked out."""
    return CallHandler(
        spy_log=spy_log,
        stub_store=stub_store,
    )


def test_handle_call_with_no_stubbing(
    decoy: Decoy,
    spy_log: SpyLog,
    stub_store: StubStore,
    subject: CallHandler,
) -> None:
    """It should noop and add the call to the stack if no stubbing is configured."""
    spy_call = SpyEvent(
        spy=SpyInfo(id=42, name="spy_name", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    behavior = None

    decoy.when(stub_store.get_by_call(spy_call)).then_return(behavior)

    result = subject.handle(spy_call)

    assert result is None
    decoy.verify(spy_log.push(spy_call))


def test_handle_call_with_return(
    decoy: Decoy,
    spy_log: SpyLog,
    stub_store: StubStore,
    subject: CallHandler,
) -> None:
    """It return a Stub's configured return value."""
    spy_call = SpyEvent(
        spy=SpyInfo(id=42, name="spy_name", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    behavior = StubBehavior(return_value="hello world")

    decoy.when(stub_store.get_by_call(spy_call)).then_return(behavior)

    result = subject.handle(spy_call)

    assert result == CallHandlerResult("hello world")
    decoy.verify(spy_log.push(spy_call))


def test_handle_call_with_raise(
    decoy: Decoy,
    spy_log: SpyLog,
    stub_store: StubStore,
    subject: CallHandler,
) -> None:
    """It raise a Stub's configured error."""
    spy_call = SpyEvent(
        spy=SpyInfo(id=42, name="spy_name", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    behavior = StubBehavior(error=RuntimeError("oh no"))

    decoy.when(stub_store.get_by_call(spy_call)).then_return(behavior)

    with pytest.raises(RuntimeError, match="oh no"):
        subject.handle(spy_call)

    decoy.verify(spy_log.push(spy_call))


def test_handle_call_with_action(
    decoy: Decoy,
    stub_store: StubStore,
    subject: CallHandler,
) -> None:
    """It should trigger a stub's configured action."""
    action = decoy.mock(name="action")
    spy_call = SpyEvent(
        spy=SpyInfo(id=42, name="spy_name", is_async=False),
        payload=SpyCall(args=(1,), kwargs={"foo": "bar"}),
    )
    behavior = StubBehavior(action=action)

    decoy.when(stub_store.get_by_call(spy_call)).then_return(behavior)
    decoy.when(action(1, foo="bar")).then_return("hello world")

    result = subject.handle(spy_call)

    assert result == CallHandlerResult("hello world")


def test_handle_prop_get_with_action(
    decoy: Decoy,
    stub_store: StubStore,
    subject: CallHandler,
) -> None:
    """It should trigger a prop get stub's configured action."""
    action = decoy.mock(name="action")
    spy_call = SpyEvent(
        spy=SpyInfo(id=42, name="spy_name", is_async=False),
        payload=SpyPropAccess(prop_name="prop", access_type=PropAccessType.GET),
    )
    behavior = StubBehavior(action=action)

    decoy.when(stub_store.get_by_call(spy_call)).then_return(behavior)
    decoy.when(action()).then_return("hello world")

    result = subject.handle(spy_call)

    assert result == CallHandlerResult("hello world")


def test_handle_call_with_context_enter(
    decoy: Decoy,
    spy_log: SpyLog,
    stub_store: StubStore,
    subject: CallHandler,
) -> None:
    """It should return a Stub's configured context value."""
    spy_call = SpyEvent(
        spy=SpyInfo(id=42, name="spy_name", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    behavior = StubBehavior(context_value="hello world")

    decoy.when(stub_store.get_by_call(spy_call)).then_return(behavior)

    with subject.handle(spy_call).value as result:  # type: ignore[union-attr]
        assert result == "hello world"

    decoy.verify(spy_log.push(spy_call))


def test_handle_call_with_context_enter_none(
    decoy: Decoy,
    spy_log: SpyLog,
    stub_store: StubStore,
    subject: CallHandler,
) -> None:
    """It should allow a configured context value to be None."""
    spy_call = SpyEvent(
        spy=SpyInfo(id=42, name="spy_name", is_async=False),
        payload=SpyCall(args=(), kwargs={}),
    )
    behavior = StubBehavior(context_value=None)

    decoy.when(stub_store.get_by_call(spy_call)).then_return(behavior)

    with subject.handle(spy_call).value as result:  # type: ignore[union-attr]
        assert result is None

    decoy.verify(spy_log.push(spy_call))
