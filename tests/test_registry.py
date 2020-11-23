"""Tests for the decoy registry."""
import pytest
from gc import collect as collect_garbage
from mock import call, MagicMock, Mock
from typing import Any

from decoy.registry import Registry
from decoy.stub import Stub


@pytest.fixture
def registry() -> Registry:
    """Get a Registry."""
    return Registry()


def test_register_decoy(registry: Registry) -> None:
    """It should register a decoy and return a unique identifier."""
    decoy_1 = MagicMock()
    decoy_2 = MagicMock()
    decoy_id_1 = registry.register_decoy(decoy_1)
    decoy_id_2 = registry.register_decoy(decoy_2)

    assert decoy_id_1 != decoy_id_2
    assert registry.get_decoy(decoy_id_1) == decoy_1
    assert registry.get_decoy(decoy_id_2) == decoy_2


def test_get_decoy_with_no_decoy(registry: Registry) -> None:
    """Peek should return None if the ID does not match."""
    result = registry.get_decoy(42)
    assert result is None


def test_peek_decoy_last_call(registry: Registry) -> None:
    """It should be able to peek the last decoy call by ID."""
    decoy = MagicMock()
    decoy_id = registry.register_decoy(decoy)

    decoy.method(foo="hello", bar="world")

    result = registry.peek_decoy_last_call(decoy_id)
    assert result == call.method(foo="hello", bar="world")

    result = registry.peek_decoy_last_call(decoy_id)
    assert result == call.method(foo="hello", bar="world")


def test_peek_decoy_last_call_with_no_decoy(registry: Registry) -> None:
    """Peek should return None if the ID does not match."""
    result = registry.peek_decoy_last_call(42)
    assert result is None


def test_pop_decoy_last_call(registry: Registry) -> None:
    """It should be able to pop the last decoy call by ID."""
    decoy = MagicMock()
    decoy_id = registry.register_decoy(decoy)

    decoy.method(foo="hello", bar="world")

    result = registry.pop_decoy_last_call(decoy_id)
    assert result == call.method(foo="hello", bar="world")

    result = registry.pop_decoy_last_call(decoy_id)
    assert result is None


def test_pop_decoy_last_call_with_no_decoy(registry: Registry) -> None:
    """Pop should return None if the ID does not match."""
    result = registry.pop_decoy_last_call(42)
    assert result is None


def test_register_stub(registry: Registry) -> None:
    """It should register a decoy and return a unique identifier."""
    decoy = MagicMock()
    decoy_id = registry.register_decoy(decoy)

    stub_1 = Stub[Any](call(1, 2, 3))
    stub_2 = Stub[Any](call(4, 5, 6))

    assert registry.get_decoy_stubs(decoy_id) == []

    registry.register_stub(decoy_id=decoy_id, stub=stub_1)
    registry.register_stub(decoy_id=decoy_id, stub=stub_2)

    assert registry.get_decoy_stubs(decoy_id) == [stub_1, stub_2]


def test_registered_decoys_clean_up_automatically(registry: Registry) -> None:
    """It should clean up when the decoy goes out of scope."""
    decoy = Mock()
    stub = Stub[Any](call(1, 2, 3))

    decoy_id = registry.register_decoy(decoy)
    registry.register_stub(decoy_id, stub)

    decoy(foo="hello", bar="world")

    # decoy goes out of scope and garbage is collected
    del decoy
    collect_garbage()

    # registry no longer has references to the decoy not its stubs
    assert registry.get_decoy(decoy_id) is None
    assert registry.get_decoy_stubs(decoy_id) == []
