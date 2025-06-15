from typing import Generic

from ..errors import VerifyError
from .event import AttributeEvent, CallEvent, MatchOptions, match_event_list
from .state import DecoyState, MockInfo
from .types import ParamsT, ReturnT


class Verify(Generic[ParamsT]):
    def __init__(
        self,
        mock: MockInfo,
        state: DecoyState,
        match_options: MatchOptions,
    ) -> None:
        self._mock = mock
        self._state = state
        self._match_options = match_options

    def called_with(self, *args: ParamsT.args, **kwargs: ParamsT.kwargs) -> None:
        expected = CallEvent(args=args, kwargs=kwargs)
        actual_events = self._state.get_events(self._mock)
        matches_event = match_event_list(actual_events, expected, self._match_options)

        if not matches_event:
            raise VerifyError(
                self._mock.name,
                self._match_options,
                expected,
                actual_events,
            )


class AttributeVerify(Generic[ReturnT]):
    def __init__(
        self,
        mock: MockInfo,
        attribute: str,
        state: DecoyState,
    ) -> None:
        self._mock = mock
        self._attribute = attribute
        self._state = state
        self._match_options = MatchOptions(
            times=None,
            ignore_extra_args=False,
            is_entered=False,
        )

    def set_with(self, value: ReturnT) -> None:
        expected = AttributeEvent.set(self._attribute, value)
        self._verify(expected)

    def delete(self) -> None:
        expected = AttributeEvent.delete(self._attribute)
        self._verify(expected)

    def _verify(self, expected: AttributeEvent) -> None:
        actual_events = self._state.get_events(self._mock)
        matches_event = match_event_list(actual_events, expected, self._match_options)

        if not matches_event:
            raise VerifyError(
                self._mock.name,
                self._match_options,
                expected,
                actual_events,
            )
