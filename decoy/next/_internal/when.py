from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Never,
    ParamSpec,
    TypeVar,
    overload,
)

from .event import AttributeEvent, Behavior, CallEvent, Event, MatchOptions
from .inspect import bind_args, ensure_callable
from .state import DecoyState, MockInfo

CallableSpecT = TypeVar("CallableSpecT", covariant=True)
AttributeSpecT = TypeVar("AttributeSpecT")
ParamsT = ParamSpec("ParamsT")
ReturnT = TypeVar("ReturnT")
ContextValueT = TypeVar("ContextValueT")


class Stub(Generic[ParamsT, ReturnT, ContextValueT]):
    def __init__(
        self,
        state: DecoyState,
        mock: MockInfo,
        match_options: MatchOptions,
        event: Event,
    ) -> None:
        self._state = state
        self._mock = mock
        self._match_options = match_options
        self._event = event

    def then_return(self, *values: ReturnT) -> None:
        behaviors = [Behavior(return_value=value) for value in values]
        self._push_behaviors(behaviors)

    def then_enter_with(self, *values: ContextValueT) -> None:
        behaviors = [Behavior(context=value) for value in values]
        self._push_behaviors(behaviors)

    def then_raise(self, *errors: Exception) -> None:
        behaviors = [Behavior(error=error) for error in errors]
        self._push_behaviors(behaviors)

    def then_do(self, *actions: Callable[ParamsT, ReturnT]) -> None:
        behaviors = [
            Behavior(action=ensure_callable(action, is_async=self._mock.is_async))
            for action in actions
        ]
        self._push_behaviors(behaviors)

    def _push_behaviors(self, behaviors: list[Behavior]) -> None:
        self._state.push_behaviors(
            self._mock,
            self._match_options,
            self._event,
            behaviors,
        )


class When(Generic[CallableSpecT, AttributeSpecT]):
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
        self: "When[Callable[ParamsT, ReturnT], Callable[..., AbstractAsyncContextManager[ContextValueT] | AbstractContextManager[ContextValueT]]]",
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, ReturnT, ContextValueT]: ...

    @overload
    def called_with(
        self: "When[Callable[ParamsT, Awaitable[ReturnT]], Any]",
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, ReturnT | Awaitable[ReturnT], Never]: ...

    @overload
    def called_with(
        self: "When[Callable[ParamsT, ReturnT], Any]",
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, ReturnT, Never]: ...

    def called_with(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Stub[Any, Any, Any]:
        bound_args = bind_args(self._mock.signature, args, kwargs)
        event = CallEvent(args=bound_args.args, kwargs=bound_args.kwargs)

        return self._create_stub(event)

    def get(self) -> Stub[[], AttributeSpecT, Never]:
        return self._create_stub(AttributeEvent.get())

    def set_with(self, value: AttributeSpecT) -> Stub[[AttributeSpecT], None, Never]:
        return self._create_stub(AttributeEvent.set(value))

    def delete(self) -> Stub[[], None, Never]:
        return self._create_stub(AttributeEvent.delete())

    def _create_stub(self, event: Event) -> Stub[Any, Any, Never]:
        return Stub(self._state, self._mock, self._match_options, event)
