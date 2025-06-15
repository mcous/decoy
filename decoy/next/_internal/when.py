from typing import (
    AsyncContextManager,
    Callable,
    ContextManager,
    Generic,
    NamedTuple,
    Union,
)

from .event import AttributeEvent, Behavior, CallEvent, Event, MatchOptions
from .state import DecoyState, MockInfo
from .types import ContextValueT, ParamsT, ReturnT


class StubConfig(NamedTuple):
    mock: MockInfo
    event: Event
    match_options: MatchOptions


class SideEffectStub(Generic[ParamsT, ReturnT]):
    def __init__(self, state: DecoyState, config: StubConfig) -> None:
        self._state = state
        self._config = config

    def then_raise(self, *errors: Exception) -> None:
        behaviors = [Behavior(error=error) for error in errors]
        self._state.push_behaviors(*self._config, behaviors)

    def then_do(self, *actions: Callable[ParamsT, ReturnT]) -> None:
        behaviors = [Behavior(action=action) for action in actions]
        self._state.push_behaviors(*self._config, behaviors)


class Stub(SideEffectStub[ParamsT, ReturnT], Generic[ParamsT, ReturnT]):
    def then_return(self, *values: ReturnT) -> None:
        behaviors = [Behavior(return_value=value) for value in values]
        self._state.push_behaviors(*self._config, behaviors)

    def then_enter_with(
        self: Union[
            "Stub[ParamsT, ContextManager[ContextValueT]]",
            "Stub[ParamsT, AsyncContextManager[ContextValueT]]",
        ],
        *values: ContextValueT,
    ) -> None:
        behaviors = [Behavior(context=context) for context in values]
        self._state.push_behaviors(*self._config, behaviors)


class When(Generic[ParamsT, ReturnT]):
    def __init__(
        self,
        mock: MockInfo,
        state: DecoyState,
        match_options: MatchOptions,
    ) -> None:
        self._mock = mock
        self._state = state
        self._match_options = match_options

    def called_with(
        self, *args: ParamsT.args, **kwargs: ParamsT.kwargs
    ) -> Stub[ParamsT, ReturnT]:
        event = CallEvent(args=args, kwargs=kwargs)
        config = StubConfig(
            mock=self._mock,
            match_options=self._match_options,
            event=event,
        )

        return Stub(self._state, config)


class AttributeWhen(Generic[ReturnT]):
    def __init__(self, mock: MockInfo, attribute: str, state: DecoyState) -> None:
        self._mock = mock
        self._attribute = attribute
        self._state = state
        self._match_options = MatchOptions(
            times=None,
            ignore_extra_args=False,
            is_entered=False,
        )

    def get(self) -> Stub[[], ReturnT]:
        event = AttributeEvent.get(self._attribute)
        config = self._create_stub_config(event)

        return Stub(self._state, config)

    def set_with(self, value: ReturnT) -> SideEffectStub[[ReturnT], None]:
        event = AttributeEvent.set(self._attribute, value)
        config = self._create_stub_config(event)

        return SideEffectStub(self._state, config)

    def delete(self) -> SideEffectStub[[], None]:
        event = AttributeEvent.delete(self._attribute)
        config = self._create_stub_config(event)

        return SideEffectStub(self._state, config)

    def _create_stub_config(self, event: AttributeEvent) -> StubConfig:
        return StubConfig(
            mock=self._mock,
            match_options=self._match_options,
            event=event,
        )
