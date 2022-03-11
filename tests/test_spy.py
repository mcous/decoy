"""Tests for spies and spy creation."""
import pytest
import inspect
import sys
from decoy import Decoy

from decoy.call_handler import CallHandler, CallHandlerResult
from decoy.spec import Spec, BoundArgs
from decoy.spy import SpyCreator, Spy, AsyncSpy
from decoy.spy_events import SpyCall, SpyEvent, SpyPropAccess, PropAccessType

from .common import SomeClass, some_func


pytestmark = pytest.mark.asyncio


@pytest.fixture()
def call_handler(decoy: Decoy) -> CallHandler:
    """Get a mock CallHandler."""
    return decoy.mock(cls=CallHandler)


@pytest.fixture()
def spy_creator(decoy: Decoy) -> SpyCreator:
    """Get a mock SpyCreator."""
    return decoy.mock(cls=SpyCreator)


@pytest.fixture()
def spec(decoy: Decoy) -> Spec:
    """Get a mock Spec."""
    return decoy.mock(cls=Spec)


def test_create_spy(decoy: Decoy, call_handler: CallHandler) -> None:
    """It should get default configurations from the spec."""
    spec = decoy.mock(cls=Spec)
    sig = inspect.signature(some_func)

    decoy.when(spec.get_full_name()).then_return("hello.world")
    decoy.when(spec.get_signature()).then_return(sig)
    decoy.when(spec.get_class_type()).then_return(SomeClass)

    subject = SpyCreator(call_handler=call_handler)
    result = subject.create(spec=spec, name="foo")

    assert isinstance(result, Spy)
    assert isinstance(result, SomeClass)
    assert inspect.signature(result) == sig
    assert repr(result) == "<Decoy mock `hello.world`>"


def test_create_async_spy(decoy: Decoy, call_handler: CallHandler) -> None:
    """It should get default configurations from the spec."""
    spec = decoy.mock(cls=Spec)

    decoy.when(spec.get_is_async()).then_return(True)

    subject = SpyCreator(call_handler=call_handler)
    result = subject.create(spec=spec)

    assert isinstance(result, AsyncSpy)


def test_child_spy(
    decoy: Decoy,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
) -> None:
    """It should create a child spy."""
    parent_spec = decoy.mock(cls=Spec)
    child_spec = decoy.mock(cls=Spec)
    child_spy = decoy.mock(cls=Spy)

    decoy.when(parent_spec.get_child_spec("child")).then_return(child_spec)
    decoy.when(spy_creator.create(spec=child_spec, is_async=False)).then_return(
        child_spy
    )

    subject = Spy(
        spec=parent_spec,
        call_handler=call_handler,
        spy_creator=spy_creator,
    )

    result = subject.child
    assert result is child_spy


def test_child_spy_caching(
    decoy: Decoy,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
) -> None:
    """It should create a child spy only once."""
    parent_spec = decoy.mock(cls=Spec)
    child_spec = decoy.mock(cls=Spec)
    child_spy = decoy.mock(cls=Spy)
    wrong_spy = decoy.mock(cls=Spy)

    decoy.when(parent_spec.get_child_spec("child")).then_return(child_spec)
    decoy.when(spy_creator.create(spec=child_spec, is_async=False)).then_return(
        child_spy,
        wrong_spy,
    )

    subject = Spy(
        spec=parent_spec,
        call_handler=call_handler,
        spy_creator=spy_creator,
    )

    assert subject.child is child_spy
    assert subject.child is child_spy


def test_spy_calls(
    decoy: Decoy,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
    spec: Spec,
) -> None:
    """It should send any calls to the call handler."""
    subject = Spy(spec=spec, call_handler=call_handler, spy_creator=spy_creator)

    decoy.when(spec.get_name()).then_return("spy_name")
    decoy.when(spec.bind_args(1, 2, three=3)).then_return(
        BoundArgs(args=(1, 2, 3), kwargs={})
    )
    decoy.when(
        call_handler.handle(
            SpyEvent(
                spy_id=id(subject),
                spy_name="spy_name",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            )
        )
    ).then_return(CallHandlerResult(42))

    result = subject(1, 2, three=3)

    assert result == 42


def test_spy_context_manager(
    decoy: Decoy,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
    spec: Spec,
) -> None:
    """It should be usable in a `with` statement."""
    enter_spec = decoy.mock(cls=Spec)
    exit_spec = decoy.mock(cls=Spec)
    enter_spy = decoy.mock(cls=Spy)
    exit_spy = decoy.mock(cls=Spy)
    error = RuntimeError("oh no")

    decoy.when(spec.get_name()).then_return("spy_name")
    decoy.when(spec.get_child_spec("__enter__")).then_return(enter_spec)
    decoy.when(spec.get_child_spec("__exit__")).then_return(exit_spec)
    decoy.when(spy_creator.create(spec=enter_spec, is_async=False)).then_return(
        enter_spy
    )
    decoy.when(spy_creator.create(spec=exit_spec, is_async=False)).then_return(exit_spy)
    decoy.when(enter_spy()).then_return(42)

    subject = Spy(spec=spec, call_handler=call_handler, spy_creator=spy_creator)
    tb = None

    try:
        with subject as result:
            assert result == 42
            raise error
    except RuntimeError:
        tb = sys.exc_info()[2]
        pass

    decoy.verify(exit_spy(RuntimeError, error, tb))


async def test_spy_async_context_manager(
    decoy: Decoy,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
    spec: Spec,
) -> None:
    """It should be usable in an `async with` statement."""
    enter_spec = decoy.mock(cls=Spec)
    exit_spec = decoy.mock(cls=Spec)
    enter_spy = decoy.mock(cls=AsyncSpy)
    exit_spy = decoy.mock(cls=AsyncSpy)
    error = RuntimeError("oh no")

    decoy.when(spec.get_name()).then_return("spy_name")
    decoy.when(spec.get_child_spec("__aenter__")).then_return(enter_spec)
    decoy.when(spec.get_child_spec("__aexit__")).then_return(exit_spec)
    decoy.when(spy_creator.create(spec=enter_spec, is_async=True)).then_return(
        enter_spy
    )
    decoy.when(spy_creator.create(spec=exit_spec, is_async=True)).then_return(exit_spy)
    decoy.when(await enter_spy()).then_return(42)

    subject = Spy(spec=spec, call_handler=call_handler, spy_creator=spy_creator)
    tb = None

    try:
        async with subject as result:
            assert result == 42
            raise error
    except RuntimeError:
        tb = sys.exc_info()[2]
        pass

    decoy.verify(await exit_spy(RuntimeError, error, tb))


def test_spy_prop_get(
    decoy: Decoy,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
    spec: Spec,
) -> None:
    """It should record a property get call."""
    subject = Spy(spec=spec, call_handler=call_handler, spy_creator=spy_creator)

    decoy.when(spec.get_name()).then_return("spy_name")
    decoy.when(
        call_handler.handle(
            SpyEvent(
                spy_id=id(subject),
                spy_name="spy_name",
                payload=SpyPropAccess(
                    prop_name="some_property",
                    access_type=PropAccessType.GET,
                ),
            ),
        )
    ).then_return(CallHandlerResult(42))

    result = subject.some_property

    assert result == 42
