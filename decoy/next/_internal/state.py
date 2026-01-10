import collections
import contextlib
from typing import Dict, List, NamedTuple, Optional

from .event import (
    MISSING,
    AttributeEvent,
    Behavior,
    CallEvent,
    Event,
    EventAndState,
    EventState,
    MatchOptions,
    match_event,
)
from .inspect import Signature


class MockInfo(NamedTuple):
    id: int
    name: str
    is_async: bool
    signature: Optional[Signature]


class EventEntry(NamedTuple):
    mock: MockInfo
    event: Event
    event_state: EventState


class BehaviorEntry(NamedTuple):
    mock: MockInfo
    event: Event
    match_options: MatchOptions
    behavior: Behavior


class DecoyState:
    def __init__(self) -> None:
        self._events: List[EventEntry] = []
        self._behaviors: List[BehaviorEntry] = []
        self._behavior_usage_by_index: Dict[int, int] = collections.defaultdict(int)

    def get_events(self, mock: MockInfo) -> List[EventAndState]:
        return [
            EventAndState(entry.event, entry.event_state)
            for entry in self._events
            if entry.mock.id == mock.id
        ]

    def push_behaviors(
        self,
        mock: MockInfo,
        match_options: MatchOptions,
        event: Event,
        behaviors: List[Behavior],
    ) -> None:
        for reversed_index, behavior in enumerate(reversed(behaviors)):
            times = (
                1
                if match_options.times is None and reversed_index != 0
                else match_options.times
            )
            entry_options = match_options._replace(times=times)
            self._behaviors.append(
                BehaviorEntry(mock, event, entry_options, behavior),
            )

    def _get_behavior(
        self,
        mock: MockInfo,
        event: Event,
        event_state: EventState,
    ) -> Optional[Behavior]:
        for reversed_index, entry in enumerate(reversed(self._behaviors)):
            index = len(self._behaviors) - reversed_index - 1
            matches_mock = entry.mock.id == mock.id
            matches_event = match_event(
                event,
                event_state,
                entry.event,
                entry.match_options,
            )

            if matches_mock and matches_event:
                usage_count = self._behavior_usage_by_index[index]

                if (
                    entry.match_options.times is None
                    or usage_count < entry.match_options.times
                ):
                    self._behavior_usage_by_index[index] = usage_count + 1
                    return entry.behavior

        return None

    def use_behavior(
        self,
        *,
        mock: MockInfo,
        event: Event,
        event_state: EventState,
        default_return_value: object = None,
    ) -> object:
        behavior = self._get_behavior(mock, event, event_state)

        if isinstance(event, CallEvent):
            args = event.args
            kwargs = event.kwargs
        elif isinstance(event, AttributeEvent) and event.value is not MISSING:
            args = (event.value,)
            kwargs = {}
        else:
            args = ()
            kwargs = {}

        self._events.append(EventEntry(mock, event, event_state))

        if behavior is None:
            return default_return_value

        if behavior.error:
            raise behavior.error

        if behavior.action:
            return behavior.action(*args, **kwargs)

        if behavior.context is not MISSING:
            return contextlib.nullcontext(behavior.context)

        return behavior.return_value

    def reset(self) -> None:
        self._events.clear()
        self._behaviors.clear()
        self._behavior_usage_by_index.clear()
