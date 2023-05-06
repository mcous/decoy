"""Smoke and acceptance tests for main Decoy interface."""
import contextlib
from typing import Any, AsyncIterator, ContextManager, Generator, Optional

import pytest

from decoy import Decoy, errors
from decoy.spy import AsyncSpy, Spy

from .fixtures import (
    SomeAsyncClass,
    SomeClass,
    SomeNestedClass,
    some_func,
    some_async_func,
)


def test_decoy_creates_spy(decoy: Decoy) -> None:
    """It should be able to create a Spy from a class."""
    subject = decoy.mock(cls=SomeClass)

    assert isinstance(subject, SomeClass)
    assert isinstance(subject, Spy)


def test_decoy_creates_func_spy(decoy: Decoy) -> None:
    """It should be able to create a Spy from a function."""
    subject = decoy.mock(func=some_func)

    assert isinstance(subject, Spy)


def test_decoy_creates_specless_spy(decoy: Decoy) -> None:
    """It should be able to create a spec-less spy."""
    subject = decoy.mock(name="subject")

    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `subject`>"


def test_decoy_creates_specless_async_spy(decoy: Decoy) -> None:
    """It should be able to create an async specless spy."""
    subject = decoy.mock(name="subject", is_async=True)

    assert isinstance(subject, AsyncSpy)


def test_decoy_mock_name_required(decoy: Decoy) -> None:
    """A name should be required for the mock."""
    with pytest.raises(errors.MockNameRequiredError):
        decoy.mock()  # type: ignore[call-overload]


@pytest.mark.filterwarnings("ignore::decoy.warnings.MiscalledStubWarning")
def test_when_then_return(decoy: Decoy) -> None:
    """It should be able to configure a stub return with a rehearsal."""
    subject = decoy.mock(func=some_func)

    decoy.when(subject("hello")).then_return("hello world")

    result = subject(val="hello")
    assert result == "hello world"

    result = subject(val="hello")
    assert result == "hello world"

    result = subject("asdfghjkl")
    assert result is None


def test_when_then_raise(decoy: Decoy) -> None:
    """It should be able to configure a stub raise with a rehearsal."""
    subject = decoy.mock(func=some_func)

    decoy.when(subject("goodbye")).then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        subject("goodbye")


def test_when_then_do(decoy: Decoy) -> None:
    """It should be able to configure a stub action with a rehearsal."""
    subject = decoy.mock(func=some_func)
    action_result = None

    def _then_do_action(arg: str) -> str:
        nonlocal action_result
        action_result = arg
        return "hello from the other side"

    decoy.when(subject("what's up")).then_do(_then_do_action)

    result = subject("what's up")
    assert action_result == "what's up"
    assert result == "hello from the other side"


async def test_when_then_do_async(decoy: Decoy) -> None:
    """It should be able to configure a stub action with a rehearsal."""
    subject = decoy.mock(func=some_async_func)
    action_result = None

    async def _then_do_action(arg: str) -> str:
        nonlocal action_result
        action_result = arg
        return "hello from the other side"

    decoy.when(await subject("what's up")).then_do(_then_do_action)

    result = await subject("what's up")
    assert action_result == "what's up"
    assert result == "hello from the other side"


def test_when_ignore_extra_args(decoy: Decoy) -> None:
    """It should be able to ignore extra args in a stub rehearsal."""

    def _get_a_thing(id: str, default: Optional[int] = None) -> int:
        raise NotImplementedError("intentionally unimplemented")

    subject = decoy.mock(func=_get_a_thing)

    decoy.when(subject("some-id"), ignore_extra_args=True).then_return(42)

    result = subject("some-id", 101)
    assert result == 42


def test_verify(decoy: Decoy) -> None:
    """It should be able to configure a verification with a rehearsal."""
    subject = decoy.mock(func=some_func)

    subject("hello")

    decoy.verify(subject("hello"))
    decoy.verify(subject(val="hello"))

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject("goodbye"))


def test_verify_times(decoy: Decoy) -> None:
    """It should be able to verify a call count."""
    subject = decoy.mock(func=some_func)

    subject("hello")

    decoy.verify(subject("hello"), times=1)
    decoy.verify(subject("goodbye"), times=0)

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject("hello"), times=0)

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject("hello"), times=2)


def test_verify_ignore_extra_args(decoy: Decoy) -> None:
    """It should be able to ignore extra args in a stub rehearsal."""

    def _get_a_thing(id: str, default: Optional[int] = None) -> int:
        raise NotImplementedError("intentionally unimplemented")

    subject = decoy.mock(func=_get_a_thing)

    subject("some-id", 101)

    decoy.verify(
        subject("some-id"),
        ignore_extra_args=True,
    )

    with pytest.raises(errors.VerifyError):
        decoy.verify(
            subject("wrong-id"),
            ignore_extra_args=True,
        )


def test_verify_call_list(decoy: Decoy) -> None:
    """It should be able to verify multiple calls."""
    subject_1 = decoy.mock(cls=SomeClass)
    subject_2 = decoy.mock(cls=SomeNestedClass)

    subject_1.foo("hello")
    subject_2.child.bar(1, 2.0, "3")
    subject_1.foo("goodbye")

    decoy.verify(
        subject_1.foo("hello"),
        subject_2.child.bar(1, 2.0, "3"),
        subject_1.foo("goodbye"),
    )

    with pytest.raises(errors.VerifyError):
        decoy.verify(
            subject_1.foo("hello"),
            subject_1.foo("goodbye"),
            subject_2.child.bar(1, 2.0, "3"),
        )


async def test_when_async(decoy: Decoy) -> None:
    """It should be able to stub an async method."""
    subject = decoy.mock(cls=SomeAsyncClass)

    decoy.when(await subject.foo("hello")).then_return("world")
    decoy.when(await subject.bar(0, 1.0, "2")).then_raise(ValueError("oh no"))

    assert await subject.foo("hello") == "world"

    with pytest.raises(ValueError, match="oh no"):
        await subject.bar(0, 1.0, "2")


async def test_verify_async(decoy: Decoy) -> None:
    """It should be able to configure a verification with an async rehearsal."""
    subject = decoy.mock(cls=SomeAsyncClass)

    await subject.foo("hello")

    decoy.verify(await subject.foo("hello"))

    with pytest.raises(AssertionError):
        decoy.verify(await subject.foo("goodbye"))


def test_reset(decoy: Decoy) -> None:
    """It should be able to reset its state."""
    subject = decoy.mock(cls=SomeClass)

    subject.foo("hello")
    decoy.reset()

    with pytest.raises(AssertionError):
        decoy.verify(subject.foo("hello"))


def test_generator_context_manager_mock(decoy: Decoy) -> None:
    """It should be able to mock a generator-based context manager."""

    class _ValueReader:
        def get_value(self) -> int:
            raise NotImplementedError()

    class _ValueReaderLoader:
        @contextlib.contextmanager
        def get_value_reader(self) -> Generator[_ValueReader, None, None]:
            raise NotImplementedError()

    value_reader_loader = decoy.mock(cls=_ValueReaderLoader)
    value_reader = decoy.mock(cls=_ValueReader)

    decoy.when(value_reader_loader.get_value_reader()).then_enter_with(value_reader)
    decoy.when(value_reader.get_value()).then_return(42)

    with value_reader_loader.get_value_reader() as subject:
        result = subject.get_value()

    assert result == 42


async def test_async_generator_context_manager_mock(decoy: Decoy) -> None:
    """It should be able to mock a generator-based context manager."""

    class _ValueReader:
        def get_value(self) -> int:
            raise NotImplementedError()

    class _ValueReaderLoader:
        @contextlib.asynccontextmanager
        async def get_value_reader(self) -> AsyncIterator[_ValueReader]:
            raise NotImplementedError()
            yield

    value_reader_loader = decoy.mock(cls=_ValueReaderLoader)
    value_reader = decoy.mock(cls=_ValueReader)

    decoy.when(value_reader_loader.get_value_reader()).then_enter_with(value_reader)
    decoy.when(value_reader.get_value()).then_return(42)

    async with value_reader_loader.get_value_reader() as subject:
        result = subject.get_value()

    assert result == 42


def test_context_manager_mock(decoy: Decoy) -> None:
    """It should be able to mock a context manager."""

    class _ValueReader(ContextManager[Any]):
        def __enter__(self) -> "_ValueReader":
            raise NotImplementedError()

        def __exit__(self, *args: Any) -> None:
            raise NotImplementedError()

        def get_value(self) -> int:
            raise NotImplementedError()

    value_reader = decoy.mock(cls=_ValueReader)

    def _handle_enter() -> _ValueReader:
        decoy.when(value_reader.get_value()).then_return(42)
        return value_reader

    def _handle_exit(*args: Any) -> None:
        decoy.when(value_reader.get_value()).then_raise(
            AssertionError("Context manager exited")
        )

    decoy.when(value_reader.__enter__()).then_do(_handle_enter)
    decoy.when(value_reader.__exit__(None, None, None)).then_do(_handle_exit)

    with value_reader as subject:
        result = subject.get_value()

    assert result == 42

    with pytest.raises(AssertionError, match="exited"):
        subject.get_value()


async def test_async_context_manager_mock(decoy: Decoy) -> None:
    """It should be able to mock an async context manager."""

    class _ValueReader(ContextManager[Any]):
        async def __aenter__(self) -> "_ValueReader":
            raise NotImplementedError()

        async def __aexit__(self, *args: Any) -> None:
            raise NotImplementedError()

        def get_value(self) -> int:
            raise NotImplementedError()

    value_reader = decoy.mock(cls=_ValueReader)

    def _handle_enter() -> _ValueReader:
        decoy.when(value_reader.get_value()).then_return(42)
        return value_reader

    def _handle_exit(*args: Any) -> None:
        decoy.when(value_reader.get_value()).then_raise(
            AssertionError("Context manager exited")
        )

    decoy.when(await value_reader.__aenter__()).then_do(_handle_enter)
    decoy.when(await value_reader.__aexit__(None, None, None)).then_do(_handle_exit)

    async with value_reader as subject:
        result = subject.get_value()

    assert result == 42

    with pytest.raises(AssertionError, match="exited"):
        subject.get_value()


async def test_async_context_manager_mock_no_spec(decoy: Decoy) -> None:
    """It should be able to mock an async context manager, even without a spec."""
    value_reader = decoy.mock(name="value_reader")

    def _handle_enter() -> Any:
        decoy.when(value_reader.get_value()).then_return(42)
        return value_reader

    def _handle_exit(*args: Any) -> None:
        decoy.when(value_reader.get_value()).then_raise(
            AssertionError("Context manager exited")
        )

    decoy.when(await value_reader.__aenter__()).then_do(_handle_enter)
    decoy.when(await value_reader.__aexit__(None, None, None)).then_do(_handle_exit)

    async with value_reader as subject:
        result = subject.get_value()

    assert result == 42

    with pytest.raises(AssertionError, match="exited"):
        subject.get_value()


def test_property_getter_stub_then_return(decoy: Decoy) -> None:
    """It should be able to stub a property getter."""
    subject = decoy.mock(name="subject")
    decoy.when(subject.prop_name).then_return(42)

    assert subject.prop_name == 42


def test_property_getter_stub_then_return_multiple(decoy: Decoy) -> None:
    """It should be able to stub a property getter with multiple return values."""
    subject = decoy.mock(name="subject")
    decoy.when(subject.prop_name).then_return(43, 44)

    assert subject.prop_name == 43
    assert subject.prop_name == 44
    assert subject.prop_name == 44


def test_property_getter_stub_then_do(decoy: Decoy) -> None:
    """It should be able to stub a property getter to act."""

    def _handle_get(*args: Any, **kwargs: Any) -> int:
        return 84

    subject = decoy.mock(name="subject")
    decoy.when(subject.prop_name).then_do(_handle_get)

    assert subject.prop_name == 84


def test_property_getter_stub_then_raise(decoy: Decoy) -> None:
    """It should be able to stub a property getter to raise."""
    subject = decoy.mock(name="subject")

    decoy.when(subject.prop_name).then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        subject.prop_name  # noqa: B018


def test_property_getter_stub_reconfigure(decoy: Decoy) -> None:
    """It should be able to reconfigure a property getter."""
    subject = decoy.mock(name="subject")

    decoy.when(subject.prop_name).then_return(42)
    assert subject.prop_name == 42

    decoy.when(subject.prop_name).then_return(43)
    assert subject.prop_name == 43


def test_property_setter_stub_then_raise(decoy: Decoy) -> None:
    """It should be able to stub a property setter to raise."""
    subject = decoy.mock(name="subject")
    prop_rehearser = decoy.prop(subject.prop_name)

    decoy.when(prop_rehearser.set(42)).then_raise(ValueError("oh no"))

    subject.prop_name = 41
    assert subject.prop_name == 41

    with pytest.raises(ValueError, match="oh no"):
        subject.prop_name = 42


def test_property_deleter_stub_then_rase(decoy: Decoy) -> None:
    """It should be able to stub a property deleter to raise."""
    subject = decoy.mock(name="subject")
    prop_rehearser = decoy.prop(subject.prop_name)

    decoy.when(prop_rehearser.delete()).then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        del subject.prop_name


def test_verify_property_access(decoy: Decoy) -> None:
    """It should be able to verify property setters and deleters."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_1.hello("world")
    subject_1.some_property = "fizzbuzz"
    del subject_2.another_property
    subject_2.answer(42)

    decoy.verify(
        subject_1.hello("world"),
        decoy.prop(subject_1.some_property).set("fizzbuzz"),
        decoy.prop(subject_2.another_property).delete(),
        subject_2.answer(42),
    )

    with pytest.raises(errors.VerifyError):
        decoy.verify(
            subject_1.hello("world"),
            decoy.prop(subject_1.some_property).set("fizzbuzz"),
            subject_2.answer(42),
            decoy.prop(subject_2.another_property).delete(),
        )
