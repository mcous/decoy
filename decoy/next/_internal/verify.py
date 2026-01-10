from typing import Any, Callable, Generic, ParamSpec, TypeVar

from ..errors import VerifyError
from .event import AttributeEvent, CallEvent, Event, MatchOptions, match_event_list
from .inspect import bind_args
from .state import DecoyState, MockInfo

SpecT = TypeVar("SpecT")
ParamsT = ParamSpec("ParamsT")


class Verify(Generic[SpecT]):
    def __init__(
        self,
        state: DecoyState,
        mock: MockInfo,
        match_options: MatchOptions,
    ) -> None:
        self._mock = mock
        self._state = state
        self._match_options = match_options

    def called_with(
        self: "Verify[Callable[ParamsT, Any]]",
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> None:
        bound_args = bind_args(self._mock.signature, args, kwargs)
        expected = CallEvent(args=bound_args.args, kwargs=bound_args.kwargs)

        self._verify(expected)

    def set_with(self, value: SpecT) -> None:
        expected = AttributeEvent.set(value)

        self._verify(expected)

    def delete(self) -> None:
        expected = AttributeEvent.delete()

        self._verify(expected)

    def _verify(self, expected: Event) -> None:
        actual_events = self._state.get_events(self._mock)
        matches_event = match_event_list(actual_events, expected, self._match_options)

        if not matches_event:
            raise VerifyError(
                self._mock.name,
                self._match_options,
                expected,
                actual_events,
            )
