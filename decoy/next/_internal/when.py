from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    Callable,
    ContextManager,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)

from .event import AttributeEvent, Behavior, CallEvent, Event, MatchOptions
from .inspect import bind_args, ensure_callable
from .state import DecoyState, MockInfo
from .types import CallableT, ContextValueT, ParamsT, ReturnT


class EffectsStub(Generic[ParamsT, ReturnT]):
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

    def then_raise(self, *errors: Exception) -> None:
        behaviors = [Behavior(error=error) for error in errors]
        self._push_behaviors(behaviors)

    def then_do(self, *actions: Callable[ParamsT, ReturnT]) -> None:
        behaviors = [
            Behavior(action=ensure_callable(action, is_async=self._mock.is_async))
            for action in actions
        ]
        self._push_behaviors(behaviors)

    def _push_behaviors(self, behaviors: List[Behavior]) -> None:
        self._state.push_behaviors(
            self._mock,
            self._match_options,
            self._event,
            behaviors,
        )


class Stub(EffectsStub[ParamsT, ReturnT], Generic[ParamsT, ReturnT]):
    def then_return(self, *values: ReturnT) -> None:
        behaviors = [Behavior(return_value=value) for value in values]
        self._push_behaviors(behaviors)

    def then_enter_with(
        self: Union[
            "Stub[ParamsT, ContextManager[ContextValueT]]",
            "Stub[ParamsT, AsyncContextManager[ContextValueT]]",
        ],
        *values: ContextValueT,
    ) -> None:
        behaviors = [Behavior(context=context) for context in values]
        self._push_behaviors(behaviors)


SpecT = TypeVar("SpecT")

ContextManagerSpecT = TypeVar("ContextManagerSpecT", bound=ContextManager[Any])


class When(Generic[SpecT]):
    def __init__(
        self,
        state: DecoyState,
        mock: MockInfo,
        match_options: MatchOptions,
    ) -> None:
        self._state = state
        self._mock = mock
        self._match_options = match_options

    def called_with(
        self: "When[CallableT[ParamsT, ReturnT]]",
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, ReturnT]:
        bound_args = bind_args(self._mock.signature, args, kwargs)
        event = CallEvent(args=bound_args.args, kwargs=bound_args.kwargs)

        return self._create_stub(event)

    def entered(
        self: "When[ContextManagerSpecT]",
    ) -> Stub[[], Any]:
        raise NotImplementedError()

    def exited_with(
        self: "When[ContextManager[Any]]",
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Stub[
        [
            Optional[Type[BaseException]],
            Optional[BaseException],
            Optional[TracebackType],
        ],
        Optional[bool],
    ]:
        raise NotImplementedError()

    def get(self) -> Stub[[], SpecT]:
        return self._create_stub(AttributeEvent.get())

    def set_with(self, value: SpecT) -> EffectsStub[[SpecT], None]:
        return self._create_stub(AttributeEvent.set(value))

    def delete(self) -> EffectsStub[[], None]:
        return self._create_stub(AttributeEvent.delete())

    def _create_stub(self, event: Event) -> Stub[Any, Any]:
        return Stub(self._state, self._mock, self._match_options, event)
