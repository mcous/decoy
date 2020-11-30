"""Decoy test double stubbing and verification library."""
from typing import cast, Any, Optional, Type

from .registry import Registry
from .spy import create_spy, SpyCall
from .stub import Stub
from .types import ClassT, FuncT, ReturnT


class Decoy:
    """Decoy test double state container."""

    _registry: Registry

    def __init__(self) -> None:
        """Initialize the state container for test doubles and stubs.

        You should initialize a new Decoy instance for every test.

        Example:
            ```python
            import pytest
            from decoy import Decoy

            @pytest.fixture
            def decoy() -> Decoy:
                return Decoy()
            ```
        """
        self._registry = Registry()

    def create_decoy(self, spec: Type[ClassT], *, is_async: bool = False) -> ClassT:
        """Create a class decoy for `spec`.

        Arguments:
            spec: A class definition that the decoy should mirror.
            is_async: Force the returned spy to be asynchronous. In most cases,
                this argument is unnecessary, since the Spy will use `spec` to
                determine if a method should be asynchronous.

        Returns:
            A spy typecast as an instance of `spec`.

        Example:
            ```python
            def test_get_something(decoy: Decoy):
                db = decoy.create_decoy(spec=Database)
                # ...
            ```

        """
        spy = create_spy(
            spec=spec, is_async=is_async, handle_call=self._handle_spy_call
        )
        self._registry.register_spy(spy)

        return cast(ClassT, spy)

    def create_decoy_func(
        self, spec: Optional[FuncT] = None, *, is_async: bool = False
    ) -> FuncT:
        """Create a function decoy for `spec`.

        Arguments:
            spec: A function that the decoy should mirror.
            is_async: Force the returned spy to be asynchronous. In most cases,
                this argument is unnecessary, since the Spy will use `spec` to
                determine if the function should be asynchronous.

        Returns:
            A spy typecast as `spec` function.

        Example:
            ```python
            def test_create_something(decoy: Decoy):
                gen_id = decoy.create_decoy_func(spec=generate_unique_id)
                # ...
            ```
        """
        spy = create_spy(
            spec=spec, is_async=is_async, handle_call=self._handle_spy_call
        )
        self._registry.register_spy(spy)

        return cast(FuncT, spy)

    def when(self, _rehearsal_result: ReturnT) -> Stub[ReturnT]:
        """Create a [Stub][decoy.stub.Stub] configuration using a rehearsal call.

        See [stubbing](/#stubbing) for more details.

        Arguments:
            _rehearsal_result: The return value of a rehearsal, used for typechecking.

        Returns:
            A stub to configure using `then_return` or `then_raise`.

        Example:
            ```python
            db = decoy.create_decoy(spec=Database)
            decoy.when(db.exists("some-id")).then_return(True)
            ```

        Note:
            The "rehearsal" is an actual call to the test fake. The fact that
            the call is written inside `when` is purely for typechecking and
            API sugar. Decoy will pop the last call to _any_ fake off its
            call stack, which will end up being the call inside `when`.
        """
        rehearsal = self._pop_last_rehearsal()
        stub = Stub[ReturnT](rehearsal=rehearsal)

        self._registry.register_stub(rehearsal.spy_id, stub)

        return stub

    def verify(self, _rehearsal_result: Optional[ReturnT] = None) -> None:
        """Verify a decoy was called using a rehearsal.

        See [verification](/#verification) for more details.

        Arguments:
            _rehearsal_result: The return value of a rehearsal, unused.

        Example:
            ```python
            def test_create_something(decoy: Decoy):
                gen_id = decoy.create_decoy_func(spec=generate_unique_id)

                # ...

                decoy.verify(gen_id("model-prefix_"))
            ```

        Note:
            The "rehearsal" is an actual call to the test fake. The fact that
            the call is written inside `verify` is purely for typechecking and
            API sugar. Decoy will pop the last call to _any_ fake off its
            call stack, which will end up being the call inside `verify`.
        """
        rehearsal = self._pop_last_rehearsal()

        assert rehearsal in self._registry.get_calls_by_spy_id(rehearsal.spy_id)

    def _pop_last_rehearsal(self) -> SpyCall:
        rehearsal = self._registry.pop_last_call()

        if rehearsal is None:
            raise ValueError("when/verify must be called with a decoy rehearsal")

        return rehearsal

    def _handle_spy_call(self, call: SpyCall) -> Any:
        self._registry.register_call(call)

        stubs = self._registry.get_stubs_by_spy_id(call.spy_id)

        for stub in reversed(stubs):
            if stub._rehearsal == call:
                return stub._act()

        return None
