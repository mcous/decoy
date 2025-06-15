import collections
import contextlib
from typing import Dict, Generator, List, NamedTuple, Optional, Union, final

from .event import (
    AttributeEvent,
    AttributeEventType,
    Behavior,
    CallEvent,
    Event,
    EventAndState,
    EventState,
    MatchOptions,
    match_event,
)


class MockInfo(NamedTuple):
    id: int
    name: str


class EventEntry(NamedTuple):
    mock: MockInfo
    event: Event
    event_state: EventState


class BehaviorEntry(NamedTuple):
    mock: MockInfo
    event: Event
    match_options: MatchOptions
    behavior: Behavior


class AttributeRehearsal(NamedTuple):
    mock: MockInfo
    attribute: str


@final
class NOT_REHEARSING: ...


class DecoyState:
    def __init__(self) -> None:
        self._events: List[EventEntry] = []
        self._behaviors: List[BehaviorEntry] = []
        self._behavior_usage_by_index: Dict[int, int] = collections.defaultdict(int)
        self._attribute_rehearsal: Union[
            None,
            AttributeRehearsal,
            NOT_REHEARSING,
        ] = NOT_REHEARSING()

    def get_events(self, mock: MockInfo) -> List[EventAndState]:
        return [
            EventAndState(entry.event, entry.event_state)
            for entry in self._events
            if entry.mock.id == mock.id
        ]

    def push_behaviors(
        self,
        mock: MockInfo,
        event: Event,
        match_options: MatchOptions,
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

    def _use_behavior(
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

    def use_call_behavior(
        self,
        mock: MockInfo,
        call_event: CallEvent,
        event_state: EventState,
    ) -> Behavior:
        behavior = self._use_behavior(mock, call_event, event_state)
        self._events.append(EventEntry(mock, call_event, event_state))

        return behavior or Behavior()

    def use_attribute_behavior(
        self,
        mock: MockInfo,
        attribute_event: AttributeEvent,
        event_state: EventState,
    ) -> Optional[Behavior]:
        if (
            isinstance(self._attribute_rehearsal, NOT_REHEARSING)
            or attribute_event.type != AttributeEventType.GET
        ):
            behavior = self._use_behavior(mock, attribute_event, event_state)
            self._events.append(EventEntry(mock, attribute_event, event_state))

            return behavior

        self._attribute_rehearsal = AttributeRehearsal(
            mock,
            attribute_event.attribute,
        )

        return Behavior()

    def use_attribute_rehearsal(self) -> Optional[AttributeRehearsal]:
        rehearsal = self._attribute_rehearsal

        if isinstance(rehearsal, NOT_REHEARSING) or rehearsal is None:
            return None

        self._attribute_rehearsal = None
        return rehearsal

    @contextlib.contextmanager
    def rehearse_attributes(self) -> Generator[None, None, None]:
        self._attribute_rehearsal = None

        try:
            yield
        finally:
            self._attribute_rehearsal = NOT_REHEARSING()

    def reset(self) -> None:
        self._events.clear()
        self._behaviors.clear()
        self._behavior_usage_by_index.clear()
        self._attribute_rehearsal = NOT_REHEARSING()
