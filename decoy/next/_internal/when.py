import contextlib
from types import TracebackType
from typing import (
    Any,
    Callable,
    Generic,
)

from .event import (
    AttributeEvent,
    Behavior,
    CallEvent,
    ContextManagerEvent,
    Event,
    MatchOptions,
)
from .inspect import bind_args, ensure_callable
from .state import DecoyState, MockInfo
from .types import ContextValueT, ParamsT, ReturnT, SpecT


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

    def _push_behaviors(self, behaviors: list[Behavior]) -> None:
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
        self: "Stub[Any, contextlib.AbstractContextManager[ContextValueT] | contextlib.AbstractAsyncContextManager[ContextValueT]]",
        *values: ContextValueT,
    ) -> None:
        behaviors = [Behavior(context=value) for value in values]
        self._push_behaviors(behaviors)


class When(Generic[SpecT, ParamsT, ReturnT, ContextValueT]):
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
        self,
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, ReturnT]:
        bound_args = bind_args(self._mock.signature, args, kwargs)
        event = CallEvent(args=bound_args.args, kwargs=bound_args.kwargs)

        return self._create_stub(event)

    def entered(
        self,
    ) -> Stub[[], ContextValueT]:
        return self._create_stub(ContextManagerEvent.enter())

    def exited_with(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Stub[
        [
            type[BaseException] | None,
            BaseException | None,
            TracebackType | None,
        ],
        bool | None,
    ]:
        return self._create_stub(
            ContextManagerEvent.exit(exc_type, exc_value, traceback)
        )

    def get(self) -> Stub[[], SpecT]:
        return self._create_stub(AttributeEvent.get())

    def set_with(self, value: SpecT) -> EffectsStub[[SpecT], None]:
        return self._create_stub(AttributeEvent.set(value))

    def delete(self) -> EffectsStub[[], None]:
        return self._create_stub(AttributeEvent.delete())

    def _create_stub(self, event: Event) -> Stub[Any, Any]:
        return Stub(self._state, self._mock, self._match_options, event)
