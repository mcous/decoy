"""Decoy test double stubbing and verification library."""
from os import linesep
from typing import cast, Any, Callable, Optional, Sequence
from warnings import warn

from .registry import Registry
from .spy import create_spy, SpyCall
from .stub import Stub
from .types import ClassT, FuncT, ReturnT
from .warnings import MissingStubWarning


class Decoy:
    """Decoy test double state container."""

    _registry: Registry
    _warn_on_missing_stubs: bool
    _next_call_is_when_rehearsal: bool

    def __init__(
        self,
        warn_on_missing_stubs: bool = True,
    ) -> None:
        """Initialize the state container for test doubles and stubs.

        You should initialize a new Decoy instance for every test.

        Arguments:
            warn_on_missing_stubs: Trigger a warning if a stub is called
                with arguments that do not match any of its rehearsals.

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
        self._warn_on_missing_stubs = warn_on_missing_stubs
        self._next_call_is_when_rehearsal = False

    def __getattribute__(self, name: str) -> Any:
        """Proxy to catch calls to `when` and mark the subsequent spy call as a rehearsal.

        This is to ensure that rehearsal calls don't accidentally trigger a
        `MissingStubWarning`.
        """
        actual_method = super().__getattribute__(name)

        if name == "when":
            self._next_call_is_when_rehearsal = True

        return actual_method

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
        spy = create_spy(
            spec=spec, is_async=is_async, handle_call=self._handle_spy_call
        )
        self._registry.register_spy(spy)

        return cast(ClassT, spy)

    def create_decoy_func(
        self, spec: Optional[FuncT] = None, *, is_async: bool = False
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
        spy = create_spy(
            spec=spec, is_async=is_async, handle_call=self._handle_spy_call
        )
        self._registry.register_spy(spy)

        return cast(FuncT, spy)

    def when(self, _rehearsal_result: ReturnT) -> Stub[ReturnT]:
        """Create a [Stub][decoy.stub.Stub] configuration using a rehearsal call.

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
        rehearsal = self._pop_last_rehearsal()
        stub = Stub[ReturnT](rehearsal=rehearsal)

        self._registry.register_stub(rehearsal.spy_id, stub)

        return stub

    def verify(self, *_rehearsal_results: Any, times: Optional[int] = None) -> None:
        """Verify a decoy was called using one or more rehearsals.

        See [verification usage guide](../usage/verify) for more details.

        Arguments:
            _rehearsal_results: The return value of rehearsals, unused except
                to determine how many rehearsals to verify.
            times: How many times the call should appear. If `times` is specifed,
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
        if len(_rehearsal_results) > 1:
            rehearsals = list(
                reversed(
                    [self._pop_last_rehearsal() for i in range(len(_rehearsal_results))]
                )
            )
        else:
            rehearsals = [self._pop_last_rehearsal()]

        all_spies = [r.spy_id for r in rehearsals]
        all_calls = self._registry.get_calls_by_spy_id(*all_spies)

        if times is None:
            for i in range(len(all_calls)):
                call = all_calls[i]
                call_list = all_calls[i : i + len(rehearsals)]

                if call == rehearsals[0] and call_list == rehearsals:
                    return None

        elif len(rehearsals) == 1:
            matching_calls = [call for call in all_calls if call == rehearsals[0]]

            if len(matching_calls) == times:
                return None

        else:
            raise ValueError("Cannot verify multiple rehearsals when using times")

        raise AssertionError(self._build_verify_error(rehearsals, all_calls, times))

    def _pop_last_rehearsal(self) -> SpyCall:
        rehearsal = self._registry.pop_last_call()

        if rehearsal is None:
            raise ValueError("when/verify must be called with a decoy rehearsal")

        return rehearsal

    def _handle_spy_call(self, call: SpyCall) -> Any:
        self._registry.register_call(call)

        stubs = self._registry.get_stubs_by_spy_id(call.spy_id)
        is_when_rehearsal = self._next_call_is_when_rehearsal
        self._next_call_is_when_rehearsal = False

        for stub in reversed(stubs):
            if stub._rehearsal == call:
                return stub._act()

        if not is_when_rehearsal and self._warn_on_missing_stubs and len(stubs) > 0:
            warn(MissingStubWarning(call, stubs))

        return None

    def _build_verify_error(
        self,
        rehearsals: Sequence[SpyCall],
        all_calls: Sequence[SpyCall],
        times: Optional[int] = None,
    ) -> str:
        rehearsals_len = len(rehearsals)
        rehearsals_plural = rehearsals_len != 1
        times_plural = times is not None and times != 1

        all_calls_len = len(all_calls)
        all_calls_plural = all_calls_len != 1

        rehearsals_printout = linesep.join(
            [f"{n + 1}.\t{str(rehearsals[n])}" for n in range(rehearsals_len)]
        )

        all_calls_printout = linesep.join(
            [f"{n + 1}.\t{str(all_calls[n])}" for n in range(all_calls_len)]
        )

        return linesep.join(
            [
                f"Expected {f'{times} ' if times is not None else ''}"
                f"call{'s' if rehearsals_plural or times_plural else ''}:",
                rehearsals_printout,
                f"Found {all_calls_len} call{'s' if all_calls_plural else ''}:",
                all_calls_printout,
            ]
        )
