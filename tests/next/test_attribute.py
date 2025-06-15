"""Tests for stubbing and verifying attributes."""

from typing import Any

import pytest

from decoy.next import Decoy, errors


def test_when_attribute_get(decoy: Decoy) -> None:
    """It stubs out an attribute."""
    subject = decoy.mock(name="subject")

    with decoy.attribute() as attr_decoy:
        attr_decoy.when(subject.foo).get().then_return("hello")

    result = subject.foo

    assert result == "hello"


def test_when_attribute_no_mock(decoy: Decoy) -> None:
    """It errors trying to stub a non-mock."""

    class _NotAMock:
        child_attr = 42

    subject = _NotAMock()

    with decoy.attribute() as attr_decoy:
        with pytest.raises(errors.NotAMockError):
            attr_decoy.when(subject.child_attr)


def test_when_property_get_multiple(decoy: Decoy) -> None:
    """It returns multiple sequential values."""
    subject = decoy.mock(name="subject")

    with decoy.attribute() as attr_decoy:
        attr_decoy.when(subject.foo).get().then_return("hello", "world")

    result = [subject.foo, subject.foo, subject.foo]

    assert result == ["hello", "world", "world"]


def test_attribute_manual_set(decoy: Decoy) -> None:
    """An attribute may be manually set."""
    subject = decoy.mock(name="subject")
    subject.foo = "hello"

    result = subject.foo

    assert result == "hello"


def test_attribute_manual_delete(decoy: Decoy) -> None:
    """An attribute may be manually deleted."""
    subject = decoy.mock(name="subject")
    subject.foo = "hello"
    del subject.foo

    with pytest.raises(AttributeError):
        _ = subject.foo


def test_when_attribute_get_then_raise(decoy: Decoy) -> None:
    """It stubs out an attribute with an error."""
    subject = decoy.mock(name="subject")

    with decoy.attribute() as attr_decoy:
        attr_decoy.when(subject.foo).get().then_raise(Exception("oh no"))

    with pytest.raises(match="oh no"):
        _ = subject.foo


def test_when_attribute_get_then_do(decoy: Decoy) -> None:
    """It calls a function."""
    subject = decoy.mock(name="subject")

    def _action() -> str:
        return "hello world"

    with decoy.attribute() as attr_decoy:
        attr_decoy.when(subject.foo).get().then_do(_action)

    result = subject.foo

    assert result == "hello world"


def test_when_attribute_set_then_raise(decoy: Decoy) -> None:
    """It stubs out an attribute with an error."""
    subject = decoy.mock(name="subject")

    with decoy.attribute() as attr_decoy:
        attr_decoy.when(subject.foo).set_with("hello").then_raise(Exception("oh no"))

    subject.foo = "hola"

    with pytest.raises(match="oh no"):
        subject.foo = "hello"


def test_when_attribute_set_then_do(decoy: Decoy) -> None:
    """It stubs out an attribute with an error."""
    subject = decoy.mock(name="subject")
    result = ""

    def _action(value: Any) -> None:
        nonlocal result
        result = f"{value} world"

    with decoy.attribute() as attr_decoy:
        attr_decoy.when(subject.foo).set_with("hello").then_do(_action)

    subject.foo = "hello"

    assert result == "hello world"


def test_when_attribute_delete_then_raise(decoy: Decoy) -> None:
    """It stubs out an attribute with an error."""
    subject = decoy.mock(name="subject")

    with decoy.attribute() as attr_decoy:
        attr_decoy.when(subject.foo).delete().then_raise(Exception("oh no"))

    with pytest.raises(match="oh no"):
        del subject.foo


def test_when_attribute_delete_then_do(decoy: Decoy) -> None:
    """It stubs out an attribute with an error."""
    subject = decoy.mock(name="subject")
    result = ""

    def _action() -> None:
        nonlocal result
        result = "hello world"

    with decoy.attribute() as attr_decoy:
        attr_decoy.when(subject.foo).delete().then_do(_action)

    del subject.foo

    assert result == "hello world"


def test_verify_attribute_set(decoy: Decoy) -> None:
    """It verifies an attribute set."""
    subject = decoy.mock(name="subject")

    with pytest.raises(errors.VerifyError):
        with decoy.attribute() as attr_decoy:
            attr_decoy.verify(subject.foo).set_with("hello")

    subject.foo = "hello"

    with decoy.attribute() as attr_decoy:
        attr_decoy.verify(subject.foo).set_with("hello")


def test_verify_attribute_delete(decoy: Decoy) -> None:
    """It verifies an attribute set."""
    subject = decoy.mock(name="subject")

    with pytest.raises(errors.VerifyError):
        with decoy.attribute() as attr_decoy:
            attr_decoy.verify(subject.foo).delete()

    del subject.foo

    with decoy.attribute() as attr_decoy:
        attr_decoy.verify(subject.foo).delete()
