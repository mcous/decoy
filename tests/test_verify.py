"""Tests for the Decoy double creator."""
import pytest

from os import linesep
from decoy import Decoy, matchers
from .common import SomeClass, SomeNestedClass, some_func


def test_call_function_then_verify(decoy: Decoy) -> None:
    """It should be able to verify a past function call."""
    stub = decoy.create_decoy_func(spec=some_func)

    stub("hello")
    stub("goodbye")

    decoy.verify(stub("hello"))
    decoy.verify(stub("goodbye"))

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(stub("fizzbuzz"))

    assert str(error_info.value) == (
        f"Expected call:{linesep}"
        f"\tsome_func('fizzbuzz'){linesep}"
        f"Found 2 calls:{linesep}"
        f"1.\tsome_func('hello'){linesep}"
        "2.\tsome_func('goodbye')"
    )


def test_call_method_then_verify(decoy: Decoy) -> None:
    """It should be able to verify a past method call."""
    stub = decoy.create_decoy(spec=SomeClass)

    stub.foo("hello")
    stub.foo("goodbye")
    stub.bar(0, 1.0, "2")
    stub.bar(3, 4.0, "5")

    decoy.verify(stub.foo("hello"))
    decoy.verify(stub.foo("goodbye"))

    decoy.verify(stub.bar(0, 1.0, "2"))
    decoy.verify(stub.bar(3, 4.0, "5"))

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(stub.foo("fizzbuzz"))

    assert str(error_info.value) == (
        f"Expected call:{linesep}"
        f"\tSomeClass.foo('fizzbuzz'){linesep}"
        f"Found 2 calls:{linesep}"
        f"1.\tSomeClass.foo('hello'){linesep}"
        "2.\tSomeClass.foo('goodbye')"
    )

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(stub.bar(6, 7.0, "8"))

    assert str(error_info.value) == (
        f"Expected call:{linesep}"
        f"\tSomeClass.bar(6, 7.0, '8'){linesep}"
        f"Found 2 calls:{linesep}"
        f"1.\tSomeClass.bar(0, 1.0, '2'){linesep}"
        "2.\tSomeClass.bar(3, 4.0, '5')"
    )


def test_verify_with_matcher(decoy: Decoy) -> None:
    """It should still work with matchers as arguments."""
    stub = decoy.create_decoy_func(spec=some_func)

    stub("hello")

    decoy.verify(stub(matchers.StringMatching("ell")))

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(stub(matchers.StringMatching("^ell")))

    assert str(error_info.value) == (
        f"Expected call:{linesep}"
        f"\tsome_func(<StringMatching '^ell'>){linesep}"
        f"Found 1 call:{linesep}"
        "1.\tsome_func('hello')"
    )


def test_call_nested_method_then_verify(decoy: Decoy) -> None:
    """It should be able to verify a past nested method call."""
    stub = decoy.create_decoy(spec=SomeNestedClass)

    stub.child.foo("hello")
    stub.child.bar(0, 1.0, "2")

    decoy.verify(stub.child.foo("hello"))
    decoy.verify(stub.child.bar(0, 1.0, "2"))

    with pytest.raises(AssertionError):
        decoy.verify(stub.foo("fizzbuzz"))


def test_call_no_return_method_then_verify(decoy: Decoy) -> None:
    """It should be able to verify a past void method call."""
    stub = decoy.create_decoy(spec=SomeClass)

    stub.do_the_thing(True)

    decoy.verify(stub.do_the_thing(True))

    with pytest.raises(AssertionError):
        decoy.verify(stub.do_the_thing(False))
