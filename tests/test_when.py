"""Tests for the Decoy double creator."""
import pytest
from mock import MagicMock

from decoy import Decoy, matchers
from .common import SomeClass, some_func


def test_stub_function_then_return(decoy: Decoy) -> None:
    """It should be able to stub a function return."""
    stub = decoy.create_decoy_func(spec=some_func)

    decoy.when(stub("hello")).then_return("world")
    decoy.when(stub("goodbye")).then_return("so long")

    assert stub("hello") == "world"
    assert stub("goodbye") == "so long"
    assert stub("fizzbuzz") is None


def test_stub_function_then_raise(decoy: Decoy) -> None:
    """It should be able to stub a function return."""
    stub = decoy.create_decoy_func(spec=some_func)

    decoy.when(stub("fizzbuzz")).then_raise(ValueError("oh no!"))

    assert stub("hello") is None
    with pytest.raises(ValueError, match="oh no!"):
        stub("fizzbuzz")


def test_stub_method_then_return(decoy: Decoy) -> None:
    """It should be able to stub a function return."""
    stub = decoy.create_decoy(spec=SomeClass)

    decoy.when(stub.foo("hello")).then_return("world")
    decoy.when(stub.foo("goodbye")).then_return("so long")
    decoy.when(stub.bar(0, 1.0, "2")).then_return(False)
    decoy.when(stub.bar(3, 4.0, "5")).then_return(True)

    assert stub.foo("hello") == "world"
    assert stub.foo("goodbye") == "so long"
    assert stub.foo("fizzbuzz") is None
    assert stub.bar(0, 1.0, "2") is False
    assert stub.bar(3, 4.0, "5") is True
    assert stub.bar(6, 7.0, "8") is None


def test_stub_method_then_raise(decoy: Decoy) -> None:
    """It should be able to stub a function return."""
    stub = decoy.create_decoy(spec=SomeClass)

    decoy.when(stub.foo("fizzbuzz")).then_raise(ValueError("oh no!"))
    decoy.when(stub.bar(3, 4.0, "5")).then_raise(TypeError("ahh!"))

    assert stub.foo("hello") is None
    assert stub.bar(0, 1.0, "2") is None

    with pytest.raises(ValueError, match="oh no!"):
        stub.foo("fizzbuzz")
    with pytest.raises(TypeError, match="ahh!"):
        stub.bar(3, 4.0, "5")


def test_stub_with_matcher(decoy: Decoy) -> None:
    """It should still work with matchers as arguments."""
    stub = decoy.create_decoy_func(spec=some_func)

    decoy.when(stub(matchers.StringMatching("ello"))).then_return("world")

    assert stub("hello") == "world"


def test_last_stubbing_wins(decoy: Decoy) -> None:
    """It should be able to stub a function return."""
    stub = decoy.create_decoy_func(spec=some_func)

    decoy.when(stub("hello")).then_return("world")
    decoy.when(stub("hello")).then_return("goodbye")

    assert stub("hello") == "goodbye"

    decoy.when(stub("hello")).then_raise(ValueError("oh no!"))

    with pytest.raises(ValueError, match="oh no!"):
        stub("hello")


def test_stub_multiple_returns(decoy: Decoy) -> None:
    """It should be able to stub multiple return values."""
    stub = decoy.create_decoy_func(spec=some_func)

    decoy.when(stub("hello")).then_return("world", "goodbye")

    assert stub("hello") == "world"
    assert stub("hello") == "goodbye"
    assert stub("hello") == "goodbye"


def test_cannot_stub_without_rehearsal(decoy: Decoy) -> None:
    """It should require a rehearsal to stub."""
    bad_stub = MagicMock()

    # stubbing without a valid decoy should fail
    with pytest.raises(ValueError, match="rehearsal"):
        decoy.when(bad_stub("bad")).then_return("nope")
