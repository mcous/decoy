"""Test for Decoy's primary logic."""
import pytest

from decoy import Decoy
from decoy.call_handler import CallHandler
from decoy.spy_log import SpyLog
from decoy.core import DecoyCore
from decoy.spy import Spy, SpyCreator
from decoy.spy_events import (
    SpyCall,
    SpyPropAccess,
    SpyEvent,
    VerifyRehearsal,
    WhenRehearsal,
    PropRehearsal,
    PropAccessType,
)
from decoy.stub_store import StubBehavior, StubStore
from decoy.verifier import Verifier
from decoy.warning_checker import WarningChecker

from .common import SomeClass


@pytest.fixture()
def spy_creator(decoy: Decoy) -> SpyCreator:
    """Get a mock instance of a SpyCreator."""
    return decoy.mock(cls=SpyCreator)


@pytest.fixture()
def call_handler(decoy: Decoy) -> CallHandler:
    """Get a mock instance of a CallHandler."""
    return decoy.mock(cls=CallHandler)


@pytest.fixture()
def spy_log(decoy: Decoy) -> SpyLog:
    """Get a mock instance of a SpyLog."""
    return decoy.mock(cls=SpyLog)


@pytest.fixture()
def stub_store(decoy: Decoy) -> StubStore:
    """Get a mock instance of a StubStore."""
    return decoy.mock(cls=StubStore)


@pytest.fixture()
def verifier(decoy: Decoy) -> Verifier:
    """Get a mock instance of a Verifier."""
    return decoy.mock(cls=Verifier)


@pytest.fixture()
def warning_checker(decoy: Decoy) -> WarningChecker:
    """Get a mock instance of a Verifier."""
    return decoy.mock(cls=WarningChecker)


@pytest.fixture()
def subject(
    verifier: Verifier,
    warning_checker: WarningChecker,
    stub_store: StubStore,
    spy_log: SpyLog,
    call_handler: CallHandler,
    spy_creator: SpyCreator,
) -> DecoyCore:
    """Get a DecoyCore instance with its dependencies mocked out."""
    return DecoyCore(
        verifier=verifier,
        warning_checker=warning_checker,
        stub_store=stub_store,
        spy_log=spy_log,
        call_handler=call_handler,
        spy_creator=spy_creator,
    )


def test_mock_no_spec(
    decoy: Decoy,
    spy_creator: SpyCreator,
    call_handler: CallHandler,
    subject: DecoyCore,
) -> None:
    """It should create a generic spy by default."""
    spy = decoy.mock(cls=Spy)

    decoy.when(spy_creator.create(spec=None, name=None, is_async=False)).then_return(
        spy
    )

    result = subject.mock()

    assert result is spy


def test_mock_with_name(
    decoy: Decoy,
    spy_creator: SpyCreator,
    call_handler: CallHandler,
    subject: DecoyCore,
) -> None:
    """It should create a generic spy by default."""
    spy = decoy.mock(cls=Spy)

    decoy.when(
        spy_creator.create(spec=None, name="my-spy", is_async=False)
    ).then_return(spy)

    result = subject.mock(name="my-spy")

    assert result is spy


def test_mock_spec(
    decoy: Decoy,
    spy_creator: SpyCreator,
    call_handler: CallHandler,
    subject: DecoyCore,
) -> None:
    """It should create a generic spy by default."""
    spy = decoy.mock(cls=Spy)

    decoy.when(
        spy_creator.create(spec=SomeClass, name=None, is_async=False)
    ).then_return(spy)

    result = subject.mock(spec=SomeClass)

    assert result is spy


def test_when_then_return(
    decoy: Decoy,
    spy_log: SpyLog,
    stub_store: StubStore,
    subject: DecoyCore,
) -> None:
    """It should be able to register a new stubbing."""
    rehearsal = WhenRehearsal(
        spy_id=1, spy_name="my_spy", payload=SpyCall(args=(), kwargs={})
    )
    decoy.when(spy_log.consume_when_rehearsal(ignore_extra_args=False)).then_return(
        rehearsal
    )

    result = subject.when("__rehearsal__", ignore_extra_args=False)
    result.then_return("hello")

    decoy.verify(
        stub_store.add(
            rehearsal=rehearsal,
            behavior=StubBehavior(return_value="hello", once=False),
        )
    )


def test_when_then_return_multiple_values(
    decoy: Decoy,
    spy_log: SpyLog,
    stub_store: StubStore,
    subject: DecoyCore,
) -> None:
    """It should add multiple return values to a stub."""
    rehearsal = WhenRehearsal(
        spy_id=1, spy_name="my_spy", payload=SpyCall(args=(), kwargs={})
    )
    decoy.when(spy_log.consume_when_rehearsal(ignore_extra_args=False)).then_return(
        rehearsal
    )

    result = subject.when(0, ignore_extra_args=False)
    result.then_return(42, 43, 44)

    decoy.verify(
        stub_store.add(
            rehearsal=rehearsal,
            behavior=StubBehavior(return_value=44, once=False),
        ),
        stub_store.add(
            rehearsal=rehearsal,
            behavior=StubBehavior(return_value=43, once=True),
        ),
        stub_store.add(
            rehearsal=rehearsal,
            behavior=StubBehavior(return_value=42, once=True),
        ),
    )


def test_when_then_raise(
    decoy: Decoy,
    spy_log: SpyLog,
    stub_store: StubStore,
    subject: DecoyCore,
) -> None:
    """It should add a raise behavior to a stub."""
    rehearsal = WhenRehearsal(
        spy_id=1, spy_name="my_spy", payload=SpyCall(args=(), kwargs={})
    )
    decoy.when(spy_log.consume_when_rehearsal(ignore_extra_args=False)).then_return(
        rehearsal
    )

    error = RuntimeError("oh no")
    result = subject.when("__rehearsal__", ignore_extra_args=False)
    result.then_raise(error)

    decoy.verify(
        stub_store.add(
            rehearsal=rehearsal,
            behavior=StubBehavior(error=error),
        )
    )


def test_when_then_do(
    decoy: Decoy,
    spy_log: SpyLog,
    stub_store: StubStore,
    subject: DecoyCore,
) -> None:
    """It should add an action behavior to a stub."""
    rehearsal = WhenRehearsal(
        spy_id=1, spy_name="my_spy", payload=SpyCall(args=(), kwargs={})
    )
    decoy.when(spy_log.consume_when_rehearsal(ignore_extra_args=False)).then_return(
        rehearsal
    )

    action = lambda: "hello world"  # noqa: E731
    result = subject.when("__rehearsal__", ignore_extra_args=False)
    result.then_do(action)

    decoy.verify(
        stub_store.add(
            rehearsal=rehearsal,
            behavior=StubBehavior(action=action),
        )
    )


def test_when_then_enter_with(
    decoy: Decoy,
    spy_log: SpyLog,
    stub_store: StubStore,
    subject: DecoyCore,
) -> None:
    """It should be able to register a ContextManager stubbing."""
    rehearsal = WhenRehearsal(
        spy_id=1, spy_name="my_spy", payload=SpyCall(args=(), kwargs={})
    )
    decoy.when(spy_log.consume_when_rehearsal(ignore_extra_args=False)).then_return(
        rehearsal
    )

    result = subject.when("__rehearsal__", ignore_extra_args=False)
    result.then_enter_with("hello")

    decoy.verify(
        stub_store.add(
            rehearsal=rehearsal,
            behavior=StubBehavior(context_value="hello", once=False),
        )
    )


def test_when_ignore_extra_args(
    decoy: Decoy,
    spy_log: SpyLog,
    stub_store: StubStore,
    subject: DecoyCore,
) -> None:
    """It should be able to register a new stubbing."""
    rehearsal = WhenRehearsal(
        spy_id=1, spy_name="my_spy", payload=SpyCall(args=(), kwargs={})
    )
    decoy.when(spy_log.consume_when_rehearsal(ignore_extra_args=True)).then_return(
        rehearsal
    )

    result = subject.when("__rehearsal__", ignore_extra_args=True)
    result.then_return("hello")

    decoy.verify(
        stub_store.add(
            rehearsal=rehearsal,
            behavior=StubBehavior(return_value="hello", once=False),
        )
    )


def test_verify(
    decoy: Decoy,
    spy_log: SpyLog,
    verifier: Verifier,
    subject: DecoyCore,
) -> None:
    """It should be able to verify a call."""
    spy_id = 42
    rehearsal = VerifyRehearsal(
        spy_id=spy_id, spy_name="my_spy", payload=SpyCall(args=(), kwargs={})
    )
    call = SpyEvent(
        spy_id=spy_id, spy_name="my_spy", payload=SpyCall(args=(), kwargs={})
    )

    decoy.when(
        spy_log.consume_verify_rehearsals(count=1, ignore_extra_args=False)
    ).then_return([rehearsal])
    decoy.when(spy_log.get_by_rehearsals([rehearsal])).then_return([call])

    subject.verify("__rehearsal__", times=None, ignore_extra_args=False)

    decoy.verify(verifier.verify(rehearsals=[rehearsal], calls=[call], times=None))


def test_verify_multiple_calls(
    decoy: Decoy,
    spy_log: SpyLog,
    verifier: Verifier,
    subject: DecoyCore,
) -> None:
    """It should be able to verify a call."""
    spy_id_1 = 42
    spy_id_2 = 9001

    rehearsals = [
        VerifyRehearsal(
            spy_id=spy_id_1, spy_name="spy_1", payload=SpyCall(args=(), kwargs={})
        ),
        VerifyRehearsal(
            spy_id=spy_id_2, spy_name="spy_2", payload=SpyCall(args=(), kwargs={})
        ),
    ]
    calls = [
        SpyEvent(spy_id=spy_id_1, spy_name="spy_1", payload=SpyCall(args=(), kwargs={}))
    ]

    decoy.when(
        spy_log.consume_verify_rehearsals(count=2, ignore_extra_args=False)
    ).then_return(rehearsals)
    decoy.when(spy_log.get_by_rehearsals(rehearsals)).then_return(calls)

    subject.verify(
        "__rehearsal_1__",
        "__rehearsal_2__",
        times=None,
        ignore_extra_args=False,
    )

    decoy.verify(verifier.verify(rehearsals=rehearsals, calls=calls, times=None))


def test_verify_call_times(
    decoy: Decoy,
    spy_log: SpyLog,
    verifier: Verifier,
    subject: DecoyCore,
) -> None:
    """It should be able to verify the call count."""
    spy_id = 42
    rehearsal = VerifyRehearsal(
        spy_id=spy_id, spy_name="my_spy", payload=SpyCall(args=(), kwargs={})
    )
    call = SpyEvent(
        spy_id=spy_id, spy_name="my_spy", payload=SpyCall(args=(), kwargs={})
    )

    decoy.when(
        spy_log.consume_verify_rehearsals(count=1, ignore_extra_args=False)
    ).then_return([rehearsal])
    decoy.when(spy_log.get_by_rehearsals([rehearsal])).then_return([call])

    subject.verify("__rehearsal__", times=2, ignore_extra_args=False)

    decoy.verify(verifier.verify(rehearsals=[rehearsal], calls=[call], times=2))


def test_prop(
    decoy: Decoy,
    spy_log: SpyLog,
    subject: DecoyCore,
) -> None:
    """It should be able to create set and delete rehearsals."""
    rehearsal = PropRehearsal(
        spy_id=1,
        spy_name="my_spy",
        payload=SpyPropAccess(prop_name="my_prop", access_type=PropAccessType.GET),
    )

    decoy.when(spy_log.consume_prop_rehearsal()).then_return(rehearsal)

    result = subject.prop("__rehearsal__")

    result.set("hello")

    expected_set_event = SpyEvent(
        spy_id=1,
        spy_name="my_spy",
        payload=SpyPropAccess(
            prop_name="my_prop",
            access_type=PropAccessType.SET,
            value="hello",
        ),
    )
    decoy.verify(spy_log.push(expected_set_event), times=1)

    result.delete()

    expected_delete_event = SpyEvent(
        spy_id=1,
        spy_name="my_spy",
        payload=SpyPropAccess(prop_name="my_prop", access_type=PropAccessType.DELETE),
    )
    decoy.verify(spy_log.push(expected_delete_event), times=1)


def test_reset(
    decoy: Decoy,
    spy_log: SpyLog,
    stub_store: StubStore,
    warning_checker: WarningChecker,
    subject: DecoyCore,
) -> None:
    """It should reset the stores."""
    call = SpyEvent(spy_id=1, spy_name="my_spy", payload=SpyCall(args=(), kwargs={}))

    decoy.when(spy_log.get_all()).then_return([call])

    subject.reset()

    decoy.verify(
        warning_checker.check([call]),
        spy_log.clear(),
        stub_store.clear(),
    )
