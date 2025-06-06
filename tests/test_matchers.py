"""Matcher tests."""

import pytest
from collections import namedtuple
from decoy import Decoy, matchers
from typing import Any, List, NamedTuple
from .fixtures import SomeClass


class _HelloClass(NamedTuple):
    hello: str = "world"

    @property
    def goodbye(self) -> str:
        return "so long"


_HelloTuple = namedtuple("_HelloTuple", ["hello"])


def test_any_matcher() -> None:
    """It should have an "anything except None" matcher."""
    assert 1 == matchers.Anything()
    assert False == matchers.Anything()  # noqa: E712
    assert {} == matchers.Anything()
    assert [] == matchers.Anything()
    assert ("hello", "world") == matchers.Anything()
    assert SomeClass() == matchers.Anything()


def test_is_a_matcher() -> None:
    """It should have an "anything that is this type" matcher."""
    assert 1 == matchers.IsA(int)
    assert False == matchers.IsA(bool)  # noqa: E712
    assert {} == matchers.IsA(dict)
    assert [] == matchers.IsA(list)
    assert ("hello", "world") == matchers.IsA(tuple)
    assert SomeClass() == matchers.IsA(SomeClass)
    assert _HelloClass() == matchers.IsA(_HelloClass, {"hello": "world"})

    assert _HelloClass() != matchers.IsA(_HelloClass, {"hello": "warld"})
    assert _HelloClass() != matchers.IsA(_HelloClass, {"hella": "world"})


def test_is_a_matcher_checks_instance(decoy: Decoy) -> None:
    """The IsA matchers should respect isinstance logic."""
    target = decoy.mock(cls=SomeClass)
    assert target == matchers.IsA(SomeClass)


def test_is_not_matcher() -> None:
    """It should have an "anything that isn't this" matcher."""
    assert 1 == matchers.IsNot(2)
    assert False == matchers.IsNot(True)  # noqa: E712
    assert {} == matchers.IsNot({"hello": "world"})
    assert [] == matchers.IsNot(["hello", "world"])
    assert ("hello", "world") == matchers.IsNot(("hey", "there"))

    assert 1 != matchers.IsNot(1)
    assert False != matchers.IsNot(False)  # noqa: E712
    assert {} != matchers.IsNot({})
    assert [] != matchers.IsNot([])
    assert ("hello", "world") != matchers.IsNot(("hello", "world"))


def test_has_attribute_matcher() -> None:
    """It should have an "anything with these attributes" matcher."""
    assert _HelloTuple("world") == matchers.HasAttributes({"hello": "world"})
    assert _HelloClass() == matchers.HasAttributes({"hello": "world"})
    assert _HelloClass() == matchers.HasAttributes({"goodbye": "so long"})

    assert {"hello": "world"} != matchers.HasAttributes({"hello": "world"})
    assert _HelloTuple("world") != matchers.HasAttributes({"goodbye": "so long"})
    assert 1 != matchers.HasAttributes({"hello": "world"})
    assert False != matchers.HasAttributes({"hello": "world"})  # noqa: E712
    assert [] != matchers.HasAttributes({"hello": "world"})


def test_dict_matching_matcher() -> None:
    """It should have an "anything with these attributes" matcher."""
    assert {"hello": "world"} == matchers.DictMatching({"hello": "world"})
    assert {"hello": "world", "goodbye": "so long"} == matchers.DictMatching(
        {"hello": "world"}
    )
    assert {"hello": "world", "goodbye": "so long"} == matchers.DictMatching(
        {"goodbye": "so long"}
    )

    assert {"hello": "world"} != matchers.DictMatching({"goodbye": "so long"})
    assert 1 != matchers.DictMatching({"hello": "world"})
    assert False != matchers.DictMatching({"hello": "world"})  # noqa: E712
    assert [] != matchers.DictMatching({"hello": "world"})


def test_array_matching_matcher() -> None:
    """It should have an "anything with these attributes" matcher."""
    assert [1, 2, 3] == matchers.ArrayMatching([1])
    assert [1, 2, 3] == matchers.ArrayMatching([1, 2])
    assert [1, 2, 3] == matchers.ArrayMatching([1, 2, 3])
    assert [1, 2, 3] != matchers.ArrayMatching([1, 2, 3, 4])
    assert [1] != matchers.ArrayMatching([1, 2])

    assert [{"hello": "world"}, {"yoo": "man"}] == matchers.ArrayMatching(
        [{"hello": "world"}]
    )
    assert [{"hello": "world"}, {"yoo": "man"}] == matchers.ArrayMatching(
        [{"yoo": "man"}]
    )
    assert [{"hello": "world"}, {"yoo": "man"}] != matchers.ArrayMatching(
        [{"yoo": "mann"}]
    )


def test_string_matching_matcher() -> None:
    """It should have an "any string that matches" matcher."""
    assert "hello" == matchers.StringMatching("ello")
    assert "hello" != matchers.StringMatching("^ello$")


def test_error_matching_matcher() -> None:
    """It should have an "any error that matches" matcher."""
    assert RuntimeError("ah!") == matchers.ErrorMatching(RuntimeError)
    assert RuntimeError("ah!") == matchers.ErrorMatching(RuntimeError, "ah")
    assert RuntimeError("ah!") != matchers.ErrorMatching(TypeError, "ah")  # type: ignore[comparison-overlap]
    assert RuntimeError("ah!") != matchers.ErrorMatching(RuntimeError, "ah$")


def test_captor_matcher() -> None:
    """It should have a captor matcher that captures the compared value."""
    captor = matchers.Captor()
    comparisons: List[Any] = [1, False, None, {}, [], ("hello", "world"), SomeClass()]

    for i, compare in enumerate(comparisons):
        assert compare == captor
        assert captor.value is compare
        assert captor.values == comparisons[0 : i + 1]


def test_captor_matcher_raises_if_no_value() -> None:
    """The captor matcher should raise an assertion error if no value."""
    captor = matchers.Captor()

    with pytest.raises(AssertionError, match="No value captured"):
        captor.value  # noqa: B018
