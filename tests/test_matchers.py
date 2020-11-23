"""Matcher tests."""
from decoy import matchers

from .common import SomeClass


def test_any_matcher() -> None:
    """It should have an "anything except None" matcher."""
    assert 1 == matchers.Anything()
    assert False == matchers.Anything()  # noqa[E712]
    assert {} == matchers.Anything()
    assert [] == matchers.Anything()
    assert ("hello", "world") == matchers.Anything()
    assert SomeClass() == matchers.Anything()


def test_is_a_matcher() -> None:
    """It should have an "anything that is this type" matcher."""
    assert 1 == matchers.IsA(int)
    assert False == matchers.IsA(bool)  # noqa[E712]
    assert {} == matchers.IsA(dict)
    assert [] == matchers.IsA(list)
    assert ("hello", "world") == matchers.IsA(tuple)
    assert SomeClass() == matchers.IsA(SomeClass)


def test_is_not_matcher() -> None:
    """It should have an "anything that isn't this" matcher."""
    assert 1 == matchers.IsNot(2)
    assert False == matchers.IsNot(True)  # noqa[E712]
    assert {} == matchers.IsNot({"hello": "world"})
    assert [] == matchers.IsNot(["hello", "world"])
    assert ("hello", "world") == matchers.IsNot(("hey", "there"))

    assert 1 != matchers.IsNot(1)
    assert False != matchers.IsNot(False)  # noqa[E712]
    assert {} != matchers.IsNot({})
    assert [] != matchers.IsNot([])
    assert ("hello", "world") != matchers.IsNot(("hello", "world"))


def test_string_matching_matcher() -> None:
    """It should have an "any string that matches" matcher."""
    assert "hello" == matchers.StringMatching("ello")
    assert "hello" != matchers.StringMatching("^ello$")


def test_error_matching_matcher() -> None:
    """It should have an "any error that matches" matcher."""
    assert RuntimeError("ah!") == matchers.ErrorMatching(RuntimeError)
    assert RuntimeError("ah!") == matchers.ErrorMatching(RuntimeError, "ah")
    assert RuntimeError("ah!") != matchers.ErrorMatching(TypeError, "ah")
    assert RuntimeError("ah!") != matchers.ErrorMatching(RuntimeError, "ah$")
