from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Any, Awaitable, Callable, Generic, ParamSpec, TypeVar, overload

from ...errors import NotAMockError
from .inspect import bind_args, ensure_callable
from .mock import ensure_mock
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

ParamsT = ParamSpec("ParamsT")
ReturnT = TypeVar("ReturnT")
ContextValueT = TypeVar("ContextValueT")
AttributeValueT = TypeVar("AttributeValueT")


class Stub(Generic[ParamsT, ReturnT]):
    """Configure how a mock behaves [when triggered](./when.md)."""

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

    def then_enter_with(self, *values: ReturnT) -> None:
        """Mock a context manager value for a generator context manager."""
        behaviors = [Behavior(context=value) for value in values]
        self._push_behaviors(behaviors)

    def then_raise(self, *errors: Exception) -> None:
        """Mock a raised exception."""
        behaviors = [Behavior(error=error) for error in errors]
        self._push_behaviors(behaviors)

    def then_do(
        self,
        *actions: Callable[ParamsT, ReturnT | Awaitable[ReturnT]],
    ) -> None:
        """Trigger a callback function."""
        behaviors = [
            Behavior(action=ensure_callable(action, is_async=self._mock.is_async))
            for action in actions
        ]
        self._push_behaviors(behaviors)

    def _push_behaviors(self, behaviors: list[Behavior]) -> None:
        self._state.push_behaviors(self._mock, self._matcher, behaviors)


class WhenSet(Generic[AttributeValueT]):
    """Configure a stub for [setting an attribute](./attributes.md).

    Created by [`When.set`][decoy.next.When.set]; pass the value to `to`.
    """

    def __init__(
        self,
        state: DecoyState,
        mock: MockInfo,
        match_options: MatchOptions,
    ) -> None:
        self._state = state
        self._mock = mock
        self._match_options = match_options

    def to(self, value: AttributeValueT) -> Stub[[AttributeValueT], None]:
        """Configure the stub to react to the attribute being set to `value`."""
        matcher = EventMatcher(
            event=AttributeEvent.set(value), options=self._match_options
        )
        return Stub(self._state, self._mock, matcher)


class When:
    """Configure [when a mock is triggered](./when.md)."""

    def __init__(
        self,
        state: DecoyState,
        match_options: MatchOptions | None = None,
    ) -> None:
        self._state = state
        self._match_options = match_options or MatchOptions()

    def __call__(
        self,
        *,
        times: int | None = None,
        ignore_extra_args: bool = False,
        is_entered: bool | None = None,
    ) -> "When":
        """Configure the stub.

        Arguments:
            times: Limit the number of times the behavior is triggered.
            ignore_extra_args: Only partially match arguments.
            is_entered: Limit the behavior to when the mock is entered using `with`.
        """
        return When(
            self._state,
            MatchOptions(times, ignore_extra_args, is_entered),
        )

    @overload
    def called(
        self,
        mock: Callable[ParamsT, AbstractAsyncContextManager[ReturnT]],
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, ReturnT]: ...

    @overload
    def called(
        self,
        mock: Callable[ParamsT, AbstractContextManager[ReturnT]],
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, ReturnT]: ...

    @overload
    def called(
        self,
        mock: Callable[ParamsT, Awaitable[ReturnT]],
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, ReturnT]: ...

    @overload
    def called(
        self,
        mock: Callable[ParamsT, ReturnT],
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, ReturnT]: ...

    def called(
        self,
        mock: Callable[ParamsT, Any],
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> Stub[ParamsT, Any]:
        """Configure a stub to react to certain passed-in arguments.

        Raises:
            NotAMockError: `mock` is invalid.
        """
        mock_info = self._ensure_mock(mock)
        bound_args = bind_args(
            signature=mock_info.signature,
            args=args,
            kwargs=kwargs,
            ignore_extra_args=self._match_options.ignore_extra_args,
        )
        event = CallEvent(args=bound_args.args, kwargs=bound_args.kwargs)

        return self._create_stub(mock_info, event)

    def get(self, attribute: AttributeValueT) -> Stub[[], AttributeValueT]:
        """Configure a stub to react to an attribute get.

        Raises:
            NotAMockError: `attribute` is invalid.
        """
        mock_info = self._ensure_mock(attribute)
        return self._create_stub(mock_info, AttributeEvent.get())

    def set(self, attribute: AttributeValueT) -> WhenSet[AttributeValueT]:
        """Configure a stub to react to an attribute set.

        Pass the set value to [`WhenSet.to`][decoy.next.WhenSet.to].

        Raises:
            NotAMockError: `attribute` is invalid.
        """
        mock_info = self._ensure_mock(attribute)
        return WhenSet(self._state, mock_info, self._match_options)

    def delete(self, attribute: object) -> Stub[[], None]:
        """Configure a stub to react to an attribute delete.

        Raises:
            NotAMockError: `attribute` is invalid.
        """
        mock_info = self._ensure_mock(attribute)
        return self._create_stub(mock_info, AttributeEvent.delete())

    def _ensure_mock(self, mock: object) -> MockInfo:
        mock_info = ensure_mock(mock)

        if not mock_info:
            mock_info = self._state.peek_last_attribute_mock(mock)

        if not mock_info:
            raise NotAMockError(
                f"`Decoy.when` must be called with a mock, but got: {mock}"
            )

        return mock_info

    def _create_stub(self, mock: MockInfo, event: Event) -> Stub[Any, Any]:
        matcher = EventMatcher(event=event, options=self._match_options)
        return Stub(self._state, mock, matcher)
