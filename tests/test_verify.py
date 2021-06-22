"""Tests for the Decoy double creator."""
import pytest

from os import linesep
from decoy import Decoy, matchers
from .common import SomeClass, SomeNestedClass, some_func


def test_call_function_then_verify(decoy: Decoy) -> None:
    """It should be able to verify a past function call."""
    spy = decoy.create_decoy_func(spec=some_func)

    spy("hello")
    spy("goodbye")

    decoy.verify(spy("hello"))
    decoy.verify(spy("goodbye"))

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(spy("fizzbuzz"))

    assert str(error_info.value) == (
        f"Expected call:{linesep}"
        f"1.\tsome_func('fizzbuzz'){linesep}"
        f"Found 2 calls:{linesep}"
        f"1.\tsome_func('hello'){linesep}"
        "2.\tsome_func('goodbye')"
    )


def test_call_method_then_verify(decoy: Decoy) -> None:
    """It should be able to verify a past method call."""
    spy = decoy.create_decoy(spec=SomeClass)

    spy.foo("hello")
    spy.foo("goodbye")
    spy.bar(0, 1.0, "2")
    spy.bar(3, 4.0, "5")

    decoy.verify(spy.foo("hello"))
    decoy.verify(spy.foo("goodbye"))

    decoy.verify(spy.bar(0, 1.0, "2"))
    decoy.verify(spy.bar(3, 4.0, "5"))

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(spy.foo("fizzbuzz"))

    assert str(error_info.value) == (
        f"Expected call:{linesep}"
        f"1.\tSomeClass.foo('fizzbuzz'){linesep}"
        f"Found 2 calls:{linesep}"
        f"1.\tSomeClass.foo('hello'){linesep}"
        "2.\tSomeClass.foo('goodbye')"
    )

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(spy.bar(6, 7.0, "8"))

    assert str(error_info.value) == (
        f"Expected call:{linesep}"
        f"1.\tSomeClass.bar(6, 7.0, '8'){linesep}"
        f"Found 2 calls:{linesep}"
        f"1.\tSomeClass.bar(0, 1.0, '2'){linesep}"
        "2.\tSomeClass.bar(3, 4.0, '5')"
    )


def test_verify_with_matcher(decoy: Decoy) -> None:
    """It should still work with matchers as arguments."""
    spy = decoy.create_decoy_func(spec=some_func)

    spy("hello")

    decoy.verify(spy(matchers.StringMatching("ell")))

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(spy(matchers.StringMatching("^ell")))

    assert str(error_info.value) == (
        f"Expected call:{linesep}"
        f"1.\tsome_func(<StringMatching '^ell'>){linesep}"
        f"Found 1 call:{linesep}"
        "1.\tsome_func('hello')"
    )


def test_call_nested_method_then_verify(decoy: Decoy) -> None:
    """It should be able to verify a past nested method call."""
    spy = decoy.create_decoy(spec=SomeNestedClass)

    spy.child.foo("hello")
    spy.child.bar(0, 1.0, "2")

    decoy.verify(spy.child.foo("hello"))
    decoy.verify(spy.child.bar(0, 1.0, "2"))

    with pytest.raises(AssertionError):
        decoy.verify(spy.foo("fizzbuzz"))


def test_call_no_return_method_then_verify(decoy: Decoy) -> None:
    """It should be able to verify a past void method call."""
    spy = decoy.create_decoy(spec=SomeClass)

    spy.do_the_thing(True)

    decoy.verify(spy.do_the_thing(True))

    with pytest.raises(AssertionError):
        decoy.verify(spy.do_the_thing(False))


def test_verify_multiple_calls(decoy: Decoy) -> None:
    """It should be able to verify multiple calls."""
    spy = decoy.create_decoy(spec=SomeClass)
    spy_func = decoy.create_decoy_func(spec=some_func)

    spy.do_the_thing(False)
    spy.do_the_thing(True)
    spy_func("hello")

    decoy.verify(
        spy.do_the_thing(True),
        spy_func("hello"),
    )

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(
            spy.do_the_thing(False),
            spy_func("goodbye"),
        )

    assert str(error_info.value) == (
        f"Expected calls:{linesep}"
        f"1.\tSomeClass.do_the_thing(False){linesep}"
        f"2.\tsome_func('goodbye'){linesep}"
        f"Found 3 calls:{linesep}"
        f"1.\tSomeClass.do_the_thing(False){linesep}"
        f"2.\tSomeClass.do_the_thing(True){linesep}"
        "3.\tsome_func('hello')"
    )

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(
            spy_func("hello"),
            spy.do_the_thing(True),
        )

    assert str(error_info.value) == (
        f"Expected calls:{linesep}"
        f"1.\tsome_func('hello'){linesep}"
        f"2.\tSomeClass.do_the_thing(True){linesep}"
        f"Found 3 calls:{linesep}"
        f"1.\tSomeClass.do_the_thing(False){linesep}"
        f"2.\tSomeClass.do_the_thing(True){linesep}"
        "3.\tsome_func('hello')"
    )

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(
            spy.do_the_thing(True),
            spy.do_the_thing(True),
            spy_func("hello"),
        )

    assert str(error_info.value) == (
        f"Expected calls:{linesep}"
        f"1.\tSomeClass.do_the_thing(True){linesep}"
        f"2.\tSomeClass.do_the_thing(True){linesep}"
        f"3.\tsome_func('hello'){linesep}"
        f"Found 3 calls:{linesep}"
        f"1.\tSomeClass.do_the_thing(False){linesep}"
        f"2.\tSomeClass.do_the_thing(True){linesep}"
        "3.\tsome_func('hello')"
    )


def test_verify_call_count(decoy: Decoy) -> None:
    """It should be able to verify a specific call count."""
    spy = decoy.create_decoy_func(spec=some_func)

    spy("hello")
    spy("hello")

    decoy.verify(spy("hello"))
    decoy.verify(spy("hello"), times=2)
    decoy.verify(spy("goodbye"), times=0)

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(spy("hello"), times=0)

    assert str(error_info.value) == (
        f"Expected 0 calls:{linesep}"
        f"1.\tsome_func('hello'){linesep}"
        f"Found 2 calls:{linesep}"
        f"1.\tsome_func('hello'){linesep}"
        "2.\tsome_func('hello')"
    )

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(spy("hello"), times=1)

    assert str(error_info.value) == (
        f"Expected 1 call:{linesep}"
        f"1.\tsome_func('hello'){linesep}"
        f"Found 2 calls:{linesep}"
        f"1.\tsome_func('hello'){linesep}"
        "2.\tsome_func('hello')"
    )

    with pytest.raises(AssertionError) as error_info:
        decoy.verify(spy("hello"), times=3)

    assert str(error_info.value) == (
        f"Expected 3 calls:{linesep}"
        f"1.\tsome_func('hello'){linesep}"
        f"Found 2 calls:{linesep}"
        f"1.\tsome_func('hello'){linesep}"
        "2.\tsome_func('hello')"
    )


def test_verify_call_count_raises_multiple_rehearsals(decoy: Decoy) -> None:
    """It should not be able to verify call count if multiple rehearsals used."""
    spy = decoy.create_decoy_func(spec=some_func)

    with pytest.raises(ValueError, match="multiple rehearsals"):
        decoy.verify(spy("hello"), spy("goodbye"), times=1)
