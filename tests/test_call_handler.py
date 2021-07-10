"""Tests for the SpyCall handling."""
import pytest

from decoy import Decoy
from decoy.spy_calls import SpyCall
from decoy.call_stack import CallStack
from decoy.stub_store import StubStore, StubBehavior
from decoy.call_handler import CallHandler


@pytest.fixture
def call_stack(decoy: Decoy) -> CallStack:
    """Get a mock instance of a CallStack."""
    return decoy.create_decoy(spec=CallStack)


@pytest.fixture
def stub_store(decoy: Decoy) -> StubStore:
    """Get a mock instance of a StubStore."""
    return decoy.create_decoy(spec=StubStore)


@pytest.fixture
def subject(
    decoy: Decoy,
    call_stack: CallStack,
    stub_store: StubStore,
) -> CallHandler:
    """Get a CallHandler instance with its dependencies mocked out."""
    return CallHandler(
        call_stack=call_stack,
        stub_store=stub_store,
    )


def test_handle_call_with_no_stubbing(
    decoy: Decoy,
    call_stack: CallStack,
    stub_store: StubStore,
    subject: CallHandler,
) -> None:
    """It should noop and add the call to the stack if no stubbing is configured."""
    spy_call = SpyCall(spy_id=42, spy_name="spy_name", args=(), kwargs={})
    behavior = StubBehavior()

    decoy.when(stub_store.get_by_call(spy_call)).then_return(behavior)

    result = subject.handle(spy_call)

    assert result is None
    decoy.verify(call_stack.push(spy_call))


def test_handle_call_with_return(
    decoy: Decoy,
    call_stack: CallStack,
    stub_store: StubStore,
    subject: CallHandler,
) -> None:
    """It return a Stub's configured return value."""
    spy_call = SpyCall(spy_id=42, spy_name="spy_name", args=(), kwargs={})
    behavior = StubBehavior(return_value="hello world")

    decoy.when(stub_store.get_by_call(spy_call)).then_return(behavior)

    result = subject.handle(spy_call)

    assert result == "hello world"
    decoy.verify(call_stack.push(spy_call))


def test_handle_call_with_raise(
    decoy: Decoy,
    call_stack: CallStack,
    stub_store: StubStore,
    subject: CallHandler,
) -> None:
    """It return a Stub's configured return value."""
    spy_call = SpyCall(spy_id=42, spy_name="spy_name", args=(), kwargs={})
    behavior = StubBehavior(error=RuntimeError("oh no"))

    decoy.when(stub_store.get_by_call(spy_call)).then_return(behavior)

    with pytest.raises(RuntimeError, match="oh no"):
        subject.handle(spy_call)

    decoy.verify(call_stack.push(spy_call))
