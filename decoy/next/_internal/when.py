from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    NoReturn,
    ParamSpec,
    TypeVar,
    overload,
)

from .inspect import bind_args, ensure_callable
from .state import DecoyState
from .values import (
    AttributeEvent,
    Behavior,
    CallEvent,
    Event,
    EventMatcher,
    MatchOptions,
    MockInfo,
)

CallableSpecT = TypeVar("CallableSpecT", covariant=True)
AttributeSpecT = TypeVar("AttributeSpecT")
ParamsT = ParamSpec("ParamsT")
ReturnT = TypeVar("ReturnT")
ContextValueT = TypeVar("ContextValueT")


class Stub(Generic[ParamsT, ReturnT, ContextValueT]):
    """Configure how a mock behaves [when called](./when.md)."""

    def __init__(
        self,
        state: DecoyState,
        mock: MockInfo,
        matcher: EventMatcher,
    ) -> None:
        self._state = state
        self._mock = mock
        self._matcher = matcher

    def then_return(self, *values: ReturnT) -> None:
        """Mock a return value."""
        behaviors = [Behavior(return_value=value) for value in values]
        self._push_behaviors(behaviors)

    def then_enter_with(self, *values: ContextValueT) -> None:
        """Mock a context manager value for a generator context manager."""
        behaviors = [Behavior(context=value) for value in values]
        self._push_behaviors(behaviors)

    def then_raise(self, *errors: Exception) -> None:
        """Mock a raised exception."""
        behaviors = [Behavior(error=error) for error in errors]
        self._push_behaviors(behaviors)

    def then_do(self, *actions: Callable[ParamsT, ReturnT]) -> None:
        """Trigger a callback function."""
        behaviors = [
            Behavior(action=ensure_callable(action, is_async=self._mock.is_async))
            for action in actions
        ]
        self._push_behaviors(behaviors)

    def _push_behaviors(self, behaviors: list[Behavior]) -> None:
        self._state.push_behaviors(self._mock, self._matcher, behaviors)


class When(Generic[CallableSpecT, AttributeSpecT]):
    """Configure [when a mock is triggered](./when.md)."""

    def __init__(
        self,
        state: DecoyState,
        mock: MockInfo,
        match_options: MatchOptions,
    ) -> None:
        self._state = state
        self._mock = mock
        self._match_options = match_options

    @overload
    def called_with(
        self: "When[Callable[ParamsT, AbstractAsyncContextManager[ContextValueT] | AbstractContextManager[ContextValueT]], Callable[..., ReturnT]]",
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, ReturnT, ContextValueT]: ...

    @overload
    def called_with(
        self: "When[Callable[ParamsT, Awaitable[ReturnT]], Any]",
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, ReturnT | Awaitable[ReturnT], NoReturn]: ...

    @overload
    def called_with(
        self: "When[Callable[ParamsT, ReturnT], Any]",
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, ReturnT, NoReturn]: ...

    def called_with(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Stub[Any, Any, Any]:
        """Configure a stub to react to certain passed-in arguments."""
        bound_args = bind_args(
            signature=self._mock.signature,
            args=args,
            kwargs=kwargs,
            ignore_extra_args=self._match_options.ignore_extra_args,
        )
        event = CallEvent(args=bound_args.args, kwargs=bound_args.kwargs)

        return self._create_stub(event)

    def get(self) -> Stub[[], AttributeSpecT, NoReturn]:
        """Configure a stub to react to an attribute get."""
        return self._create_stub(AttributeEvent.get())

    def set(self, value: AttributeSpecT) -> Stub[[AttributeSpecT], None, NoReturn]:
        """Configure a stub to react to an attribute set."""
        return self._create_stub(AttributeEvent.set(value))

    def delete(self) -> Stub[[], None, NoReturn]:
        """Configure a stub to react to an attribute delete."""
        return self._create_stub(AttributeEvent.delete())

    def _create_stub(self, event: Event) -> Stub[Any, Any, NoReturn]:
        matcher = EventMatcher(event=event, options=self._match_options)
        return Stub(self._state, self._mock, matcher)
