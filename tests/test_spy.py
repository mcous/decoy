"""Tests for spies and spy creation."""
import pytest
import inspect
import sys

from decoy import Decoy

from decoy.call_handler import CallHandler, CallHandlerResult
from decoy.spy import AsyncSpy, Spy, SpyCreator
from decoy.spy_core import BoundArgs, SpyCore
from decoy.spy_events import SpyCall, SpyEvent, SpyInfo, SpyPropAccess, PropAccessType

from .fixtures import SomeClass, some_func


pytestmark = pytest.mark.asyncio


@pytest.fixture
def call_handler(decoy: Decoy) -> CallHandler:
    """Get a mock CallHandler."""
    return decoy.mock(cls=CallHandler)


@pytest.fixture
def spy_creator(decoy: Decoy) -> SpyCreator:
    """Get a mock SpyCreator."""
    return decoy.mock(cls=SpyCreator)


@pytest.fixture
def spy_core(decoy: Decoy) -> SpyCore:
    """Get a mock SpyCore."""
    return decoy.mock(cls=SpyCore)


def test_create_spy(decoy: Decoy, call_handler: CallHandler) -> None:
    """It should get default configurations from the spec."""
    core = decoy.mock(cls=SpyCore)
    signature = inspect.signature(some_func)

    decoy.when(core.full_name).then_return("hello.world")
    decoy.when(core.signature).then_return(signature)
    decoy.when(core.class_type).then_return(SomeClass)
    decoy.when(core.is_async).then_return(False)

    subject = SpyCreator(call_handler=call_handler)
    result = subject.create(core=core)

    assert isinstance(result, Spy)
    assert isinstance(result, SomeClass)
    assert inspect.signature(result) == signature
    assert repr(result) == "<Decoy mock `hello.world`>"


def test_create_async_spy(decoy: Decoy, call_handler: CallHandler) -> None:
    """It should get default configurations from the spec."""
    core = decoy.mock(cls=SpyCore)

    decoy.when(core.is_async).then_return(True)

    subject = SpyCreator(call_handler=call_handler)
    result = subject.create(core=core)

    assert isinstance(result, AsyncSpy)


def test_child_spy(
    decoy: Decoy,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
) -> None:
    """It should create a child spy."""
    parent_core = decoy.mock(cls=SpyCore)
    child_core = decoy.mock(cls=SpyCore)
    child_spy = decoy.mock(cls=Spy)

    decoy.when(parent_core.create_child_core("child", is_async=False)).then_return(
        child_core
    )
    decoy.when(spy_creator.create(core=child_core)).then_return(child_spy)

    subject = Spy(
        core=parent_core,
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
    parent_core = decoy.mock(cls=SpyCore)
    child_core = decoy.mock(cls=SpyCore)
    child_spy = decoy.mock(cls=Spy)
    wrong_spy = decoy.mock(cls=Spy)

    decoy.when(parent_core.create_child_core("child", is_async=False)).then_return(
        child_core
    )
    decoy.when(spy_creator.create(core=child_core)).then_return(
        child_spy,
        wrong_spy,
    )

    subject = Spy(
        core=parent_core,
        call_handler=call_handler,
        spy_creator=spy_creator,
    )

    assert subject.child is child_spy
    assert subject.child is child_spy


def test_spy_calls(
    decoy: Decoy,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
    spy_core: SpyCore,
) -> None:
    """It should send any calls to the call handler."""
    spy_info = SpyInfo(id=123456, name="spy_name", is_async=False)

    decoy.when(spy_core.info).then_return(spy_info)
    decoy.when(spy_core.bind_args(1, 2, three=3)).then_return(
        BoundArgs(args=(1, 2, 3), kwargs={})
    )
    decoy.when(
        call_handler.handle(
            SpyEvent(
                spy=spy_info,
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            )
        )
    ).then_return(CallHandlerResult(42))

    subject = Spy(core=spy_core, call_handler=call_handler, spy_creator=spy_creator)
    result = subject(1, 2, three=3)

    assert result == 42


async def test_async_spy_calls(
    decoy: Decoy,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
    spy_core: SpyCore,
) -> None:
    """It should understand async returns from the call handler."""
    spy_info = SpyInfo(id=123456, name="spy_name", is_async=True)

    async def _get_call_result() -> int:
        return 42

    decoy.when(spy_core.info).then_return(spy_info)
    decoy.when(spy_core.bind_args(1, 2, three=3)).then_return(
        BoundArgs(args=(1, 2, 3), kwargs={})
    )

    subject = AsyncSpy(
        core=spy_core,
        call_handler=call_handler,
        spy_creator=spy_creator,
    )

    decoy.when(
        call_handler.handle(
            SpyEvent(
                spy=spy_info,
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            )
        )
    ).then_return(CallHandlerResult(_get_call_result()))

    result = await subject(1, 2, three=3)

    assert result == 42


def test_spy_context_manager(
    decoy: Decoy,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
    spy_core: SpyCore,
) -> None:
    """It should be usable in a `with` statement."""
    enter_core = decoy.mock(cls=SpyCore)
    exit_core = decoy.mock(cls=SpyCore)
    enter_spy = decoy.mock(cls=Spy)
    exit_spy = decoy.mock(cls=Spy)
    error = RuntimeError("oh no")

    decoy.when(spy_core.create_child_core("__enter__", is_async=False)).then_return(
        enter_core
    )
    decoy.when(spy_core.create_child_core("__exit__", is_async=False)).then_return(
        exit_core
    )
    decoy.when(spy_creator.create(core=enter_core)).then_return(enter_spy)
    decoy.when(spy_creator.create(core=exit_core)).then_return(exit_spy)
    decoy.when(enter_spy()).then_return(42)

    subject = Spy(core=spy_core, call_handler=call_handler, spy_creator=spy_creator)
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
    spy_core: SpyCore,
) -> None:
    """It should be usable in an `async with` statement."""
    enter_core = decoy.mock(cls=SpyCore)
    exit_core = decoy.mock(cls=SpyCore)
    enter_spy = decoy.mock(cls=AsyncSpy)
    exit_spy = decoy.mock(cls=AsyncSpy)
    error = RuntimeError("oh no")

    decoy.when(spy_core.create_child_core("__aenter__", is_async=True)).then_return(
        enter_core
    )
    decoy.when(spy_core.create_child_core("__aexit__", is_async=True)).then_return(
        exit_core
    )
    decoy.when(spy_creator.create(core=enter_core)).then_return(enter_spy)
    decoy.when(spy_creator.create(core=exit_core)).then_return(exit_spy)
    decoy.when(await enter_spy()).then_return(42)

    subject = Spy(core=spy_core, call_handler=call_handler, spy_creator=spy_creator)
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
    spy_core: SpyCore,
) -> None:
    """It should record a property get call."""
    spy_info = SpyInfo(id=123456, name="spy_name", is_async=False)

    decoy.when(spy_core.info).then_return(spy_info)
    decoy.when(
        call_handler.handle(
            SpyEvent(
                spy=spy_info,
                payload=SpyPropAccess(
                    prop_name="some_property",
                    access_type=PropAccessType.GET,
                ),
            ),
        )
    ).then_return(CallHandlerResult(42))

    subject = Spy(core=spy_core, call_handler=call_handler, spy_creator=spy_creator)
    result = subject.some_property

    assert result == 42


def test_spy_prop_set(
    decoy: Decoy,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
    spy_core: SpyCore,
) -> None:
    """It should record a property set call."""
    spy_info = SpyInfo(id=123456, name="spy_name", is_async=False)

    decoy.when(spy_core.info).then_return(spy_info)

    subject = Spy(core=spy_core, call_handler=call_handler, spy_creator=spy_creator)
    subject.some_property = 42
    assert subject.some_property == 42

    decoy.verify(
        call_handler.handle(
            SpyEvent(
                spy=spy_info,
                payload=SpyPropAccess(
                    prop_name="some_property",
                    access_type=PropAccessType.SET,
                    value=42,
                ),
            ),
        )
    )


def test_spy_prop_delete(
    decoy: Decoy,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
    spy_core: SpyCore,
) -> None:
    """It should record a property set call."""
    spy_info = SpyInfo(id=123456, name="spy_name", is_async=False)

    decoy.when(spy_core.info).then_return(spy_info)

    subject = Spy(core=spy_core, call_handler=call_handler, spy_creator=spy_creator)
    subject.some_property = 42
    del subject.some_property

    assert subject.some_property != 42

    decoy.verify(
        call_handler.handle(
            SpyEvent(
                spy=spy_info,
                payload=SpyPropAccess(
                    prop_name="some_property",
                    access_type=PropAccessType.DELETE,
                ),
            ),
        )
    )
