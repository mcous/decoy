"""Decoy stubbing and spying library."""

from typing import Any, Callable, Coroutine, Generic, Optional, Union, overload

from . import errors, matchers, warnings
from .context_managers import (
    AsyncContextManager,
    AsyncGeneratorContextManager,
    ContextManager,
    GeneratorContextManager,
)
from .core import DecoyCore, PropCore, StubCore
from .types import ClassT, ContextValueT, FuncT, ReturnT

# ensure decoy does not pollute pytest tracebacks
__tracebackhide__ = True


class Decoy:
    """Decoy mock factory and state container.

    You should create a new Decoy instance before each test and call
    [`reset`][decoy.Decoy.reset] after each test. If you use the
    [`decoy` pytest fixture][decoy.pytest_plugin.decoy], this is done
    automatically. See the [setup guide][] for more details.

    !!! example
        ```python
        decoy = Decoy()

        # test your subject
        ...

        decoy.reset()
        ```

    [setup guide]: index.md#setup
    """

    def __init__(self) -> None:
        self._core = DecoyCore()

    @overload
    def mock(self, *, cls: Callable[..., ClassT]) -> ClassT: ...

    @overload
    def mock(self, *, func: FuncT) -> FuncT: ...

    @overload
    def mock(self, *, name: str, is_async: bool = False) -> Any: ...

    def mock(
        self,
        *,
        cls: Optional[Any] = None,
        func: Optional[Any] = None,
        name: Optional[str] = None,
        is_async: bool = False,
    ) -> Any:
        """Create a mock. See the [mock creation guide] for more details.

        [mock creation guide]: usage/create.md

        Arguments:
            cls: A class definition that the mock should imitate.
            func: A function definition the mock should imitate.
            name: A name to use for the mock. If you do not use
                `cls` or `func`, you should add a `name`.
            is_async: Force the returned spy to be asynchronous. This argument
                only applies if you don't use `cls` nor `func`.

        Returns:
            A spy typecast as the object it's imitating, if any.

        !!! example
            ```python
            def test_get_something(decoy: Decoy):
                db = decoy.mock(cls=Database)
                # ...
            ```
        """
        spec = cls or func

        if spec is None and name is None:
            raise errors.MockNameRequiredError.create()

        return self._core.mock(spec=spec, name=name, is_async=is_async)

    def when(
        self,
        _rehearsal_result: ReturnT,
        *,
        ignore_extra_args: bool = False,
    ) -> "Stub[ReturnT]":
        """Create a [`Stub`][decoy.Stub] configuration using a rehearsal call.

        See [stubbing usage guide](usage/when.md) for more details.

        Arguments:
            _rehearsal_result: The return value of a rehearsal, used for typechecking.
            ignore_extra_args: Allow the rehearsal to specify fewer arguments than
                the actual call. Decoy will compare and match any given arguments,
                ignoring unspecified arguments.

        Returns:
            A stub to configure using [`then_return`][decoy.Stub.then_return],
            [`then_raise`][decoy.Stub.then_raise], [`then_do`][decoy.Stub.then_do],
            or [`then_enter_with`][decoy.Stub.then_enter_with].

        !!! example
            ```python
            db = decoy.mock(cls=Database)
            decoy.when(db.exists("some-id")).then_return(True)
            ```

        !!! note
            The "rehearsal" is an actual call to the test fake. Because the
            call is written inside `when`, Decoy is able to infer that the call
            is a rehearsal for stub configuration purposes rather than a call
            from the code-under-test.
        """
        stub_core = self._core.when(
            _rehearsal_result,
            ignore_extra_args=ignore_extra_args,
        )
        return Stub(core=stub_core)

    def verify(
        self,
        *_rehearsal_results: Any,
        times: Optional[int] = None,
        ignore_extra_args: bool = False,
    ) -> None:
        """Verify a mock was called using one or more rehearsals.

        See [verification usage guide](usage/verify.md) for more details.

        Arguments:
            _rehearsal_results: The return value of rehearsals, unused except
                to determine how many rehearsals to verify.
            times: How many times the call should appear. If `times` is specified,
                the call count must match exactly, otherwise the call must appear
                at least once. The `times` argument must be used with exactly one
                rehearsal.
            ignore_extra_args: Allow the rehearsal to specify fewer arguments than
                the actual call. Decoy will compare and match any given arguments,
                ignoring unspecified arguments.

        Raises:
            VerifyError: The verification was not satisfied.

        !!! example
            ```python
            def test_create_something(decoy: Decoy):
                gen_id = decoy.mock(func=generate_unique_id)

                # ...

                decoy.verify(gen_id("model-prefix_"))
            ```

        !!! note
            A "rehearsal" is an actual call to the test fake. The fact that
            the call is written inside `verify` is purely for typechecking and
            API sugar. Decoy will pop the last call(s) to _any_ fake off its
            call stack, which will end up being the call inside `verify`.
        """
        self._core.verify(
            *_rehearsal_results,
            times=times,
            ignore_extra_args=ignore_extra_args,
        )

    def prop(self, _rehearsal_result: ReturnT) -> "Prop[ReturnT]":
        """Create property setter and deleter rehearsals.

        See [property mocking guide](advanced/properties.md) for more details.

        Arguments:
            _rehearsal_result: The property to mock, for typechecking.

        Returns:
            A prop rehearser on which you can call [`set`][decoy.Prop.set] or
            [`delete`][decoy.Prop.delete] to create property rehearsals.
        """
        prop_core = self._core.prop(_rehearsal_result)
        return Prop(core=prop_core)

    def reset(self) -> None:
        """Reset all mock state.

        This method should be called after every test to ensure spies and stubs
        don't leak between tests. The [`decoy`][decoy.pytest_plugin.decoy] fixture
        provided by the pytest plugin will call `reset` automatically.

        The `reset` method may also trigger warnings if Decoy detects any questionable
        mock usage. See [decoy.warnings][] for more details.
        """
        self._core.reset()


class Stub(Generic[ReturnT]):
    """A rehearsed Stub that can be used to configure mock behaviors.

    See [stubbing usage guide](usage/when.md) for more details.
    """

    def __init__(self, core: StubCore) -> None:
        self._core = core

    def then_return(self, *values: ReturnT) -> None:
        """Configure the stub to return value(s).

        Arguments:
            *values: Zero or more return values. Multiple values will result
                     in different return values for subsequent calls, with the
                     last value latching in once all other values have returned.
        """
        self._core.then_return(*values)

    def then_raise(self, error: Exception) -> None:
        """Configure the stub to raise an error.

        Arguments:
            error: The error to raise.

        !!! note
            Setting a stub to raise will prevent you from writing new
            rehearsals, because they will raise. If you need to make more calls
            to [`when`][decoy.Decoy.when], you'll need to wrap your rehearsal
            in a `try`.
        """
        self._core.then_raise(error)

    def then_do(
        self,
        action: Callable[..., Union[ReturnT, Coroutine[Any, Any, ReturnT]]],
    ) -> None:
        """Configure the stub to trigger an action.

        Arguments:
            action: The function to call. Called with whatever arguments
                are actually passed to the stub. May be an `async def`
                function if the mock is also asynchronous.

        Raises:
            MockNotAsyncError: `action` was an `async def` function,
                but the mock is synchronous.
        """
        self._core.then_do(action)

    @overload
    def then_enter_with(
        self: "Stub[ContextManager[ContextValueT]]",
        value: ContextValueT,
    ) -> None: ...

    @overload
    def then_enter_with(
        self: "Stub[AsyncContextManager[ContextValueT]]",
        value: ContextValueT,
    ) -> None: ...

    @overload
    def then_enter_with(
        self: "Stub[GeneratorContextManager[ContextValueT]]",
        value: ContextValueT,
    ) -> None: ...

    @overload
    def then_enter_with(
        self: "Stub[AsyncGeneratorContextManager[ContextValueT]]",
        value: ContextValueT,
    ) -> None: ...

    def then_enter_with(
        self: Union[
            "Stub[ContextManager[ContextValueT]]",
            "Stub[GeneratorContextManager[ContextValueT]]",
            "Stub[AsyncContextManager[ContextValueT]]",
            "Stub[AsyncGeneratorContextManager[ContextValueT]]",
        ],
        value: ContextValueT,
    ) -> None:
        """Configure the stub to return a value wrapped in a context manager.

        The wrapping context manager is compatible with both the synchronous and
        asynchronous context manager interfaces.

        See the [context manager usage guide](advanced/context-managers.md)
        for more details.

        Arguments:
            value: A return value to wrap in a ContextManager.
        """
        self._core.then_enter_with(value)


class Prop(Generic[ReturnT]):
    """Rehearsal creator for mocking property setters and deleters.

    See [property mocking guide](advanced/properties.md) for more details.
    """

    def __init__(self, core: PropCore) -> None:
        self._core = core

    def set(self, value: ReturnT) -> None:
        """Create a property setter rehearsal.

        By wrapping `set` in a call to [`when`][decoy.Decoy.when] or
        [`verify`][decoy.Decoy.verify], you can stub or verify a call
        to a property setter.

        Arguments:
            value: The value

        !!! example
            ```python
            some_obj = decoy.mock()
            some_obj.prop = 42
            decoy.verify(decoy.prop(some_obj.prop).set(42))
            ```
        """
        self._core.set(value)

    def delete(self) -> None:
        """Create a property deleter rehearsal.

        By wrapping `delete` in a call to [`when`][decoy.Decoy.when] or
        [`verify`][decoy.Decoy.verify], you can stub or verify a call
        to a property deleter.

        !!! example
            ```python
            some_obj = decoy.mock()
            del some_obj.prop
            decoy.verify(decoy.prop(some_obj.prop).delete())
            ```
        """
        self._core.delete()


__all__ = ["Decoy", "Prop", "Stub", "errors", "matchers", "warnings"]
