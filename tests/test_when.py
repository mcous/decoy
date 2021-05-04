"""Tests for the Decoy double creator."""
import pytest

from decoy import Decoy, matchers, warnings
from .common import some_func, SomeClass, SomeAsyncClass, SomeNestedClass


def test_stub_function_then_return(decoy: Decoy) -> None:
    """It should be able to stub a function return."""
    stub = decoy.create_decoy_func(spec=some_func)

    decoy.when(stub("hello")).then_return("world")
    decoy.when(stub("goodbye")).then_return("so long")

    assert stub("hello") == "world"
    assert stub("goodbye") == "so long"
    assert stub("fizzbuzz") is None


def test_stub_function_then_raise(decoy: Decoy) -> None:
    """It should be able to stub a function raise."""
    stub = decoy.create_decoy_func(spec=some_func)

    decoy.when(stub("fizzbuzz")).then_raise(ValueError("oh no!"))

    assert stub("hello") is None
    with pytest.raises(ValueError, match="oh no!"):
        stub("fizzbuzz")


def test_stub_method_then_return(decoy: Decoy) -> None:
    """It should be able to stub a method return."""
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
    """It should be able to stub a method raise."""
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

    decoy.when(stub(matchers.StringMatching("ell"))).then_return("world")

    assert stub("hello") == "world"


def test_last_stubbing_wins(decoy: Decoy) -> None:
    """It should return the last stubbing given identical arguments."""
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
    bad_stub = some_func

    # stubbing without a valid decoy should fail
    with pytest.raises(ValueError, match="rehearsal"):
        decoy.when(bad_stub("bad")).then_return("nope")


def test_stub_nested_method_then_return(decoy: Decoy) -> None:
    """It should be able to stub a nested method return."""
    stub = decoy.create_decoy(spec=SomeNestedClass)

    decoy.when(stub.child.foo("hello")).then_return("world")

    assert stub.child.foo("hello") == "world"
    assert stub.child.foo("goodbye") is None
    assert stub.foo("hello") is None


@pytest.mark.asyncio
async def test_stub_async_method(decoy: Decoy) -> None:
    """It should be able to stub an async method."""
    stub = decoy.create_decoy(spec=SomeAsyncClass)

    decoy.when(await stub.foo("hello")).then_return("world")
    decoy.when(await stub.bar(0, 1.0, "2")).then_raise(ValueError("oh no"))

    assert await stub.foo("hello") == "world"

    with pytest.raises(ValueError, match="oh no"):
        await stub.bar(0, 1.0, "2")


def test_stub_nested_sync_class_in_async(decoy: Decoy) -> None:
    """It should be able to stub a sync child instance of an async class."""

    class _AsyncWithSync:
        @property
        def _sync_child(self) -> SomeClass:
            ...

    stub = decoy.create_decoy(spec=_AsyncWithSync)

    decoy.when(stub._sync_child.foo("hello")).then_return("world")

    assert stub._sync_child.foo("hello") == "world"


@pytest.mark.asyncio
async def test_stub_nested_async_class_in_sync(decoy: Decoy) -> None:
    """It should be able to stub an async child instance of an sync class."""

    class _SyncWithAsync:
        @property
        def _async_child(self) -> SomeAsyncClass:
            ...

    stub = decoy.create_decoy(spec=_SyncWithAsync)

    decoy.when(await stub._async_child.foo("hello")).then_return("world")

    assert await stub._async_child.foo("hello") == "world"


def test_no_stubbing_found_warning(strict_decoy: Decoy) -> None:
    """It should raise a warning if a stub is configured and then called incorrectly."""
    stub = strict_decoy.create_decoy_func(spec=some_func)

    strict_decoy.when(stub("hello")).then_return("world")

    with pytest.warns(warnings.MissingStubWarning):
        stub("h3110")


@pytest.mark.filterwarnings("error::UserWarning")
def test_no_stubbing_found_warnings_disabled(decoy: Decoy) -> None:
    """It should not raise a warning if warn_on_missing_stub is disabled."""
    stub = decoy.create_decoy_func(spec=some_func)

    decoy.when(stub("hello")).then_return("world")

    stub("h3110")


@pytest.mark.filterwarnings("error::UserWarning")
def test_additional_stubbings_do_not_warn(strict_decoy: Decoy) -> None:
    """It should not raise a warning if warn_on_missing_stub is disabled."""
    stub = strict_decoy.create_decoy_func(spec=some_func)

    strict_decoy.when(stub("hello")).then_return("world")
    strict_decoy.when(stub("goodbye")).then_return("so long")
