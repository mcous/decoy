"""Decoy implementation logic."""
from typing import Any, Callable, Optional

from .spy import SpyConfig, SpyFactory, create_spy as default_create_spy
from .spy_calls import WhenRehearsal
from .call_stack import CallStack
from .stub_store import StubStore, StubBehavior
from .call_handler import CallHandler
from .verifier import Verifier
from .warning_checker import WarningChecker
from .types import ReturnT


class DecoyCore:
    """The DecoyCore class implements the main logic of Decoy."""

    def __init__(
        self,
        create_spy: Optional[SpyFactory] = None,
        verifier: Optional[Verifier] = None,
        warning_checker: Optional[WarningChecker] = None,
        stub_store: Optional[StubStore] = None,
        call_stack: Optional[CallStack] = None,
        call_handler: Optional[CallHandler] = None,
    ) -> None:
        """Initialize the DecoyCore with its dependencies."""
        self._create_spy = create_spy or default_create_spy
        self._verifier = verifier or Verifier()
        self._warning_checker = warning_checker or WarningChecker()
        self._stub_store = stub_store or StubStore()
        self._call_stack = call_stack or CallStack()
        self._call_hander = call_handler or CallHandler(
            call_stack=self._call_stack,
            stub_store=self._stub_store,
        )

    def mock(self, *, spec: Optional[Any] = None, is_async: bool = False) -> Any:
        """Create and register a new spy."""
        config = SpyConfig(
            spec=spec,
            is_async=is_async,
            handle_call=self._call_hander.handle,
        )
        return self._create_spy(config)

    def when(self, _rehearsal: ReturnT) -> "StubCore":
        """Create a new stub from the last spy rehearsal."""
        rehearsal = self._call_stack.consume_when_rehearsal()
        return StubCore(rehearsal=rehearsal, stub_store=self._stub_store)

    def verify(self, *_rehearsals: ReturnT, times: Optional[int] = None) -> None:
        """Verify that a Spy or Spies were called."""
        rehearsals = self._call_stack.consume_verify_rehearsals(count=len(_rehearsals))
        calls = self._call_stack.get_by_rehearsals(rehearsals)

        self._verifier.verify(rehearsals=rehearsals, calls=calls, times=times)

    def reset(self) -> None:
        """Reset and remove all stored spies and stubs."""
        calls = self._call_stack.get_all()
        self._warning_checker.check(calls)
        self._call_stack.clear()
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
