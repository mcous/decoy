"""Decoy implementation logic."""
from typing import Any, Callable, Optional

from .call_handler import CallHandler
from .spy_log import SpyLog

# from .spy import SpyConfig
from .spy import SpyCreator
from .spy_calls import WhenRehearsal
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
        calls = self._spy_log.get_by_rehearsals(rehearsals)

        self._verifier.verify(rehearsals=rehearsals, calls=calls, times=times)

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
