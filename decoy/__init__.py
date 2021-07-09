"""Decoy stubbing and spying library."""
from __future__ import annotations
from typing import cast, Any, Callable, Generic, Optional

from . import matchers, errors, warnings
from .core import DecoyCore, StubCore
from .types import ClassT, FuncT, ReturnT


class Decoy:
    """Decoy test double state container."""

    def __init__(self) -> None:
        """Initialize the state container for test doubles and stubs.

        You should initialize a new Decoy instance for every test. See the
        [setup guide](../setup) for more details.
        """
        self._core = DecoyCore()

    def create_decoy(
        self,
        spec: Callable[..., ClassT],
        *,
        is_async: bool = False,
    ) -> ClassT:
        """Create a class decoy for `spec`.

        See [decoy creation usage guide](../usage/create) for more details.

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
        spy = self._core.mock(spec=spec, is_async=is_async)
        return cast(ClassT, spy)

    def create_decoy_func(
        self,
        spec: Optional[FuncT] = None,
        *,
        is_async: bool = False,
    ) -> FuncT:
        """Create a function decoy for `spec`.

        See [decoy creation usage guide](../usage/create) for more details.

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
        spy = self._core.mock(spec=spec, is_async=is_async)
        return cast(FuncT, spy)

    def when(self, _rehearsal_result: ReturnT) -> Stub[ReturnT]:
        """Create a [Stub][decoy.Stub] configuration using a rehearsal call.

        See [stubbing usage guide](../usage/when) for more details.

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
            The "rehearsal" is an actual call to the test fake. Because the
            call is written inside `when`, Decoy is able to infer that the call
            is a rehearsal for stub configuration purposes rather than a call
            from the code-under-test.
        """
        stub_core = self._core.when(_rehearsal_result)
        return Stub(core=stub_core)

    def verify(self, *_rehearsal_results: Any, times: Optional[int] = None) -> None:
        """Verify a decoy was called using one or more rehearsals.

        See [verification usage guide](../usage/verify) for more details.

        Arguments:
            _rehearsal_results: The return value of rehearsals, unused except
                to determine how many rehearsals to verify.
            times: How many times the call should appear. If `times` is specified,
                the call count must match exactly, otherwise the call must appear
                at least once. The `times` argument must be used with exactly one
                rehearsal.

        Example:
            ```python
            def test_create_something(decoy: Decoy):
                gen_id = decoy.create_decoy_func(spec=generate_unique_id)

                # ...

                decoy.verify(gen_id("model-prefix_"))
            ```

        Note:
            A "rehearsal" is an actual call to the test fake. The fact that
            the call is written inside `verify` is purely for typechecking and
            API sugar. Decoy will pop the last call(s) to _any_ fake off its
            call stack, which will end up being the call inside `verify`.
        """
        self._core.verify(*_rehearsal_results, times=times)

    def reset(self) -> None:
        """Reset all decoy state.

        This method should be called after every test to ensure spies and stubs
        don't leak between tests. The Decoy fixture provided by the pytest plugin
        will do this automatically. See the [setup guide](../setup) for more details.

        The `reset` method may also trigger warnings if Decoy detects any questionable
        mock usage. See [decoy.warnings][] for more details.
        """
        self._core.reset()


class Stub(Generic[ReturnT]):
    """A rehearsed Stub that can be used to configure mock behaviors."""

    def __init__(self, core: StubCore) -> None:
        self._core = core

    def then_return(self, *values: ReturnT) -> None:
        """Set the stub to return value(s).

        See [stubbing usage guide](../usage/when) for more details.

        Arguments:
            *values: Zero or more return values. Multiple values will result
                     in different return values for subsequent calls, with the
                     last value latching in once all other values have returned.
        """
        self._core.then_return(*values)

    def then_raise(self, error: Exception) -> None:
        """Set the stub to raise an error.

        See [stubbing usage guide](../usage/when) for more details.

        Arguments:
            error: The error to raise.

        Note:
            Setting a stub to raise will prevent you from writing new
            rehearsals, because they will raise. If you need to make more calls
            to `when`, you'll need to wrap your rehearsal in a `try`.
        """
        self._core.then_raise(error)


__all__ = ["Decoy", "Stub", "matchers", "warnings", "errors"]
