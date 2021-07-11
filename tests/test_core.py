"""Test for Decoy's primary logic."""
import pytest

from decoy import Decoy
from decoy.core import DecoyCore
from decoy.call_handler import CallHandler
from decoy.call_stack import CallStack
from decoy.stub_store import StubStore, StubBehavior
from decoy.verifier import Verifier
from decoy.warning_checker import WarningChecker
from decoy.spy_calls import SpyCall, VerifyRehearsal, WhenRehearsal
from decoy.spy import Spy, SpyConfig, SpyFactory, create_spy as default_create_spy

from .common import SomeClass, noop


@pytest.fixture
def create_spy(decoy: Decoy) -> SpyFactory:
    """Get a mock instance of a create_spy factory function."""
    return decoy.mock(func=default_create_spy)


@pytest.fixture
def call_handler(decoy: Decoy) -> CallHandler:
    """Get a mock instance of a create_spy factory function."""
    return decoy.mock(cls=CallHandler)


@pytest.fixture
def call_stack(decoy: Decoy) -> CallStack:
    """Get a mock instance of a CallStack."""
    return decoy.mock(cls=CallStack)


@pytest.fixture
def stub_store(decoy: Decoy) -> StubStore:
    """Get a mock instance of a StubStore."""
    return decoy.mock(cls=StubStore)


@pytest.fixture
def verifier(decoy: Decoy) -> Verifier:
    """Get a mock instance of a Verifier."""
    return decoy.mock(cls=Verifier)


@pytest.fixture
def warning_checker(decoy: Decoy) -> WarningChecker:
    """Get a mock instance of a Verifier."""
    return decoy.mock(cls=WarningChecker)


@pytest.fixture
def subject(
    create_spy: SpyFactory,
    verifier: Verifier,
    warning_checker: WarningChecker,
    stub_store: StubStore,
    call_stack: CallStack,
    call_handler: CallHandler,
) -> DecoyCore:
    """Get a DecoyCore instance with its dependencies mocked out."""
    return DecoyCore(
        create_spy=create_spy,
        verifier=verifier,
        warning_checker=warning_checker,
        stub_store=stub_store,
        call_stack=call_stack,
        call_handler=call_handler,
    )


def test_mock_no_spec(
    decoy: Decoy,
    create_spy: SpyFactory,
    call_handler: CallHandler,
    subject: DecoyCore,
) -> None:
    """It should create a generic spy by default."""
    spy = Spy(handle_call=noop, name="my-spy")
    expected_config = SpyConfig(spec=None, handle_call=call_handler.handle)
    decoy.when(create_spy(expected_config)).then_return(spy)

    result = subject.mock()

    assert result is spy


def test_mock_spec(
    decoy: Decoy,
    create_spy: SpyFactory,
    call_handler: CallHandler,
    subject: DecoyCore,
) -> None:
    """It should create a generic spy by default."""
    spy = Spy(handle_call=noop, name="my-spy")
    expected_config = SpyConfig(spec=SomeClass, handle_call=call_handler.handle)

    decoy.when(create_spy(expected_config)).then_return(spy)

    result = subject.mock(spec=SomeClass)

    assert result is spy


def test_when_then_return(
    decoy: Decoy,
    call_stack: CallStack,
    stub_store: StubStore,
    subject: DecoyCore,
) -> None:
    """It should be able to register a new stubbing."""
    rehearsal = WhenRehearsal(spy_id=1, spy_name="my_spy", args=(), kwargs={})
    decoy.when(call_stack.consume_when_rehearsal()).then_return(rehearsal)

    result = subject.when("__rehearsal__")
    result.then_return("hello")

    decoy.verify(
        stub_store.add(
            rehearsal=rehearsal,
            behavior=StubBehavior(return_value="hello", once=False),
        )
    )


def test_when_then_return_multiple_values(
    decoy: Decoy,
    call_stack: CallStack,
    stub_store: StubStore,
    subject: DecoyCore,
) -> None:
    """It should add multiple return values to a stub."""
    rehearsal = WhenRehearsal(spy_id=1, spy_name="my_spy", args=(), kwargs={})
    decoy.when(call_stack.consume_when_rehearsal()).then_return(rehearsal)

    result = subject.when(0)
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
    call_stack: CallStack,
    stub_store: StubStore,
    subject: DecoyCore,
) -> None:
    """It should add a raise behavior to a stub."""
    rehearsal = WhenRehearsal(spy_id=1, spy_name="my_spy", args=(), kwargs={})
    decoy.when(call_stack.consume_when_rehearsal()).then_return(rehearsal)

    error = RuntimeError("oh no")
    result = subject.when("__rehearsal__")
    result.then_raise(error)

    decoy.verify(
        stub_store.add(
            rehearsal=rehearsal,
            behavior=StubBehavior(error=error),
        )
    )


def test_verify(
    decoy: Decoy,
    call_stack: CallStack,
    verifier: Verifier,
    subject: DecoyCore,
) -> None:
    """It should be able to verify a call."""
    spy_id = 42
    rehearsal = VerifyRehearsal(spy_id=spy_id, spy_name="my_spy", args=(), kwargs={})
    call = SpyCall(spy_id=spy_id, spy_name="my_spy", args=(), kwargs={})

    decoy.when(call_stack.consume_verify_rehearsals(count=1)).then_return([rehearsal])
    decoy.when(call_stack.get_by_rehearsals([rehearsal])).then_return([call])

    subject.verify("__rehearsal__")

    decoy.verify(verifier.verify(rehearsals=[rehearsal], calls=[call], times=None))


def test_verify_multiple_calls(
    decoy: Decoy,
    call_stack: CallStack,
    verifier: Verifier,
    subject: DecoyCore,
) -> None:
    """It should be able to verify a call."""
    spy_id_1 = 42
    spy_id_2 = 9001

    rehearsals = [
        VerifyRehearsal(spy_id=spy_id_1, spy_name="spy_1", args=(), kwargs={}),
        VerifyRehearsal(spy_id=spy_id_2, spy_name="spy_2", args=(), kwargs={}),
    ]
    calls = [SpyCall(spy_id=spy_id_1, spy_name="spy_1", args=(), kwargs={})]

    decoy.when(call_stack.consume_verify_rehearsals(count=2)).then_return(rehearsals)
    decoy.when(call_stack.get_by_rehearsals(rehearsals)).then_return(calls)

    subject.verify("__rehearsal_1__", "__rehearsal_2__")

    decoy.verify(verifier.verify(rehearsals=rehearsals, calls=calls, times=None))


def test_verify_call_times(
    decoy: Decoy,
    call_stack: CallStack,
    verifier: Verifier,
    subject: DecoyCore,
) -> None:
    """It should be able to verify the call count."""
    spy_id = 42
    rehearsal = VerifyRehearsal(spy_id=spy_id, spy_name="my_spy", args=(), kwargs={})
    call = SpyCall(spy_id=spy_id, spy_name="my_spy", args=(), kwargs={})

    decoy.when(call_stack.consume_verify_rehearsals(count=1)).then_return([rehearsal])
    decoy.when(call_stack.get_by_rehearsals([rehearsal])).then_return([call])

    subject.verify("__rehearsal__", times=2)

    decoy.verify(verifier.verify(rehearsals=[rehearsal], calls=[call], times=2))


def test_reset(
    decoy: Decoy,
    call_stack: CallStack,
    stub_store: StubStore,
    warning_checker: WarningChecker,
    subject: DecoyCore,
) -> None:
    """It should reset the stores."""
    call = SpyCall(spy_id=1, spy_name="my_spy", args=(), kwargs={})

    decoy.when(call_stack.get_all()).then_return([call])

    subject.reset()

    decoy.verify(
        warning_checker.check([call]),
        call_stack.clear(),
        stub_store.clear(),
    )
