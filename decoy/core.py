"""Decoy implementation logic."""
import inspect
from typing import Any, Callable, Optional

from .call_handler import CallHandler
from .errors import MockNotAsyncError
from .spy import SpyCreator
from .spy_events import WhenRehearsal, PropAccessType, SpyEvent, SpyInfo, SpyPropAccess
from .spy_log import SpyLog
from .stub_store import StubBehavior, StubStore
from .types import ContextValueT, ReturnT
from .verifier import Verifier
from .warning_checker import WarningChecker

# ensure decoy.core does not pollute Pytest tracebacks
__tracebackhide__ = True


class DecoyCore:
    """The DecoyCore class implements the main logic of Decoy."""

    def __init__(
        self,
        verifier: Optional[Verifier] = None,
        warning_checker: Optional[WarningChecker] = None,
        stub_store: Optional[StubStore] = None,
        spy_log: Optional[SpyLog] = None,
        call_handler: Optional[CallHandler] = None,
        spy_creator: Optional[SpyCreator] = None,
    ) -> None:
        """Initialize the DecoyCore with its dependencies."""
        self._verifier = verifier or Verifier()
        self._warning_checker = warning_checker or WarningChecker()
        self._stub_store = stub_store or StubStore()
        self._spy_log = spy_log or SpyLog()
        self._call_hander = call_handler or CallHandler(
            spy_log=self._spy_log,
            stub_store=self._stub_store,
        )
        self._spy_creator = spy_creator or SpyCreator(call_handler=self._call_hander)

    def mock(
        self,
        *,
        spec: Optional[Any] = None,
        name: Optional[str] = None,
        is_async: bool = False,
    ) -> Any:
        """Create and register a new spy."""
        return self._spy_creator.create(spec=spec, name=name, is_async=is_async)

    def when(self, _rehearsal: ReturnT, *, ignore_extra_args: bool) -> "StubCore":
        """Create a new stub from the last spy rehearsal."""
        rehearsal = self._spy_log.consume_when_rehearsal(
            ignore_extra_args=ignore_extra_args
        )
        return StubCore(rehearsal=rehearsal, stub_store=self._stub_store)

    def verify(
        self,
        *_rehearsals: ReturnT,
        times: Optional[int],
        ignore_extra_args: bool,
    ) -> None:
        """Verify that a Spy or Spies were called."""
        rehearsals = self._spy_log.consume_verify_rehearsals(
            count=len(_rehearsals),
            ignore_extra_args=ignore_extra_args,
        )
        calls = self._spy_log.get_calls_to_verify([r.spy.id for r in rehearsals])

        self._verifier.verify(rehearsals=rehearsals, calls=calls, times=times)

    def prop(self, _rehearsal: ReturnT) -> "PropCore":
        """Get a property setter/deleter rehearser."""
        spy, payload = self._spy_log.consume_prop_rehearsal()

        return PropCore(spy=spy, prop_name=payload.prop_name, spy_log=self._spy_log)

    def reset(self) -> None:
        """Reset and remove all stored spies and stubs."""
        calls = self._spy_log.get_all()
        self._warning_checker.check(calls)
        self._spy_log.clear()
        self._stub_store.clear()


class StubCore:
    """The StubCore class implements the main logic of a Decoy Stub."""

    def __init__(self, rehearsal: WhenRehearsal, stub_store: StubStore) -> None:
        """Initialize the Stub with a configuration."""
        self._rehearsal = rehearsal
        self._stub_store = stub_store

    def then_return(self, *values: ReturnT) -> None:
        """Set the stub to return value(s)."""
        for i, return_value in reversed(list(enumerate(values))):
            self._stub_store.add(
                rehearsal=self._rehearsal,
                behavior=StubBehavior(
                    return_value=return_value,
                    once=(i != len(values) - 1),
                ),
            )

    def then_raise(self, error: Exception) -> None:
        """Set the stub to raise an error."""
        self._stub_store.add(
            rehearsal=self._rehearsal,
            behavior=StubBehavior(error=error),
        )

    def then_do(self, action: Callable[..., ReturnT]) -> None:
        """Set the stub to perform an action."""
        spy_info = self._rehearsal.spy

        if inspect.iscoroutinefunction(action) and not spy_info.is_async:
            raise MockNotAsyncError(
                f"Cannot configure {spy_info.name} to call {action}"
                f" because {spy_info.name} is not asynchronous."
            )

        self._stub_store.add(
            rehearsal=self._rehearsal,
            behavior=StubBehavior(action=action),
        )

    def then_enter_with(self, value: ContextValueT) -> None:
        """Set the stub to return a ContextManager wrapped value."""
        self._stub_store.add(
            rehearsal=self._rehearsal,
            behavior=StubBehavior(context_value=value),
        )


class PropCore:
    """Main logic of a property access rehearser."""

    def __init__(
        self,
        spy: SpyInfo,
        prop_name: str,
        spy_log: SpyLog,
    ) -> None:
        self._spy = spy
        self._prop_name = prop_name
        self._spy_log = spy_log

    def set(self, value: Any) -> None:
        """Create a property setter rehearsal."""
        event = SpyEvent(
            spy=self._spy,
            payload=SpyPropAccess(
                prop_name=self._prop_name,
                access_type=PropAccessType.SET,
                value=value,
            ),
        )
        self._spy_log.push(event)

    def delete(self) -> None:
        """Create a property deleter rehearsal."""
        event = SpyEvent(
            spy=self._spy,
            payload=SpyPropAccess(
                prop_name=self._prop_name,
                access_type=PropAccessType.DELETE,
            ),
        )
        self._spy_log.push(event)
