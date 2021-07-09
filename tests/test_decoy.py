"""Smoke and integration tests for main Decoy interface."""
import pytest
from decoy import Decoy
from decoy.spy import Spy

from .common import SomeClass, SomeAsyncClass, some_func


def test_decoy_creates_spy(decoy: Decoy) -> None:
    """It should be able to create a Spy from a class."""
    subject = decoy.create_decoy(spec=SomeClass)

    assert isinstance(subject, SomeClass)


def test_decoy_creates_func_spy(decoy: Decoy) -> None:
    """It should be able to create a Spy from a class."""
    subject = decoy.create_decoy_func(spec=some_func)

    assert isinstance(subject, Spy)


@pytest.mark.filterwarnings("ignore::decoy.warnings.MiscalledStubWarning")
def test_when_smoke_test(decoy: Decoy) -> None:
    """It should be able to configure a stub with a rehearsal."""
    subject = decoy.create_decoy_func(spec=some_func)

    decoy.when(subject("hello")).then_return("hello world")

    result = subject("hello")
    assert result == "hello world"

    result = subject("goodbye")
    assert result is None


def test_verify_smoke_test(decoy: Decoy) -> None:
    """It should be able to configure a verification with a rehearsal."""
    subject = decoy.create_decoy_func(spec=some_func)

    subject("hello")

    decoy.verify(subject("hello"))

    with pytest.raises(AssertionError):
        decoy.verify(subject("goodbye"))


@pytest.mark.asyncio
async def test_when_async_smoke_test(decoy: Decoy) -> None:
    """It should be able to stub an async method."""
    subject = decoy.create_decoy(spec=SomeAsyncClass)

    decoy.when(await subject.foo("hello")).then_return("world")
    decoy.when(await subject.bar(0, 1.0, "2")).then_raise(ValueError("oh no"))

    assert await subject.foo("hello") == "world"

    with pytest.raises(ValueError, match="oh no"):
        await subject.bar(0, 1.0, "2")


@pytest.mark.asyncio
async def test_verify_async_smoke_test(decoy: Decoy) -> None:
    """It should be able to configure a verification with an async rehearsal."""
    subject = decoy.create_decoy(spec=SomeAsyncClass)

    await subject.foo("hello")

    decoy.verify(await subject.foo("hello"))

    with pytest.raises(AssertionError):
        decoy.verify(await subject.foo("goodbye"))


def test_reset_smoke_test(decoy: Decoy) -> None:
    """It should be able to reset its state."""
    subject = decoy.create_decoy(spec=SomeClass)

    subject.foo("hello")
    decoy.reset()

    with pytest.raises(AssertionError):
        decoy.verify(subject.foo("hello"))
