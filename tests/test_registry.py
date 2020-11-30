"""Tests for the decoy registry."""
import pytest
from typing import Any

from decoy.spy import create_spy, SpyCall
from decoy.registry import Registry
from decoy.stub import Stub

from .common import noop


@pytest.fixture
def registry() -> Registry:
    """Get a Registry."""
    return Registry()


def test_register_spy(registry: Registry) -> None:
    """It should register a spy and return a unique identifier."""
    spy = create_spy(handle_call=noop)

    spy_id = registry.register_spy(spy)

    assert spy_id == id(spy)


def test_register_call(registry: Registry) -> None:
    """It should register a spy call."""
    spy = create_spy(handle_call=noop)
    call_1 = SpyCall(spy_id=id(spy), args=(1,), kwargs={})
    call_2 = SpyCall(spy_id=id(spy), args=(2,), kwargs={})

    registry.register_spy(spy)
    registry.register_call(call_1)
    registry.register_call(call_2)

    assert registry.last_call == call_2


def test_pop_last_call(registry: Registry) -> None:
    """It should be able to pop the last spy call."""
    spy = create_spy(handle_call=noop)
    call_1 = SpyCall(spy_id=id(spy), args=(1,), kwargs={})
    call_2 = SpyCall(spy_id=id(spy), args=(2,), kwargs={})

    registry.register_spy(spy)
    registry.register_call(call_1)
    registry.register_call(call_2)

    assert registry.pop_last_call() == call_2
    assert registry.last_call == call_1


def test_register_stub(registry: Registry) -> None:
    """It should register a stub."""
    spy = create_spy(handle_call=noop)
    spy_id = registry.register_spy(spy)
    call_1 = SpyCall(spy_id=id(spy), args=(1,), kwargs={})
    call_2 = SpyCall(spy_id=id(spy), args=(2,), kwargs={})

    stub_1 = Stub[Any](call_1)
    stub_2 = Stub[Any](call_2)

    assert registry.get_stubs_by_spy_id(spy_id) == []

    registry.register_stub(spy_id=spy_id, stub=stub_1)
    registry.register_stub(spy_id=spy_id, stub=stub_2)

    assert registry.get_stubs_by_spy_id(spy_id) == [stub_1, stub_2]


def test_registered_calls_clean_up_automatically(registry: Registry) -> None:
    """It should clean up when the spy goes out of scope."""
    spy = create_spy(handle_call=noop)
    call_1 = SpyCall(spy_id=id(spy), args=(1,), kwargs={})
    stub_1 = Stub[Any](call_1)

    spy_id = registry.register_spy(spy)
    registry.register_call(call_1)
    registry.register_stub(spy_id=spy_id, stub=stub_1)

    assert registry.last_call == call_1
    assert registry.get_stubs_by_spy_id(spy_id) == [stub_1]

    # spy goes out of scope and garbage is collected
    del spy

    # registry no longer has references to the calls
    assert registry.last_call is None
    assert registry.get_stubs_by_spy_id(spy_id) == []
