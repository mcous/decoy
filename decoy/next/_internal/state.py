import collections
import collections.abc
import contextlib
from typing import NamedTuple

from .compare import (
    is_event_from_mock,
    is_matching_count,
    is_matching_event,
    is_miscalled_stub_event,
    is_redundant_verify,
    is_successful_verify,
    is_verifiable_mock_event,
)
from .values import (
    MISSING,
    AttributeEvent,
    AttributeEventType,
    Behavior,
    BehaviorEntry,
    CallEvent,
    CallSite,
    Event,
    EventEntry,
    EventMatcher,
    EventState,
    MiscalledStub,
    MockInfo,
    VerificationEntry,
)


class VerificationResult(NamedTuple):
    is_success: bool
    is_redundant: bool
    matching_events: list[EventEntry]
    mock_events: list[EventEntry]
    order_anchor: EventEntry | None = None
    order_timeline: tuple[EventEntry, ...] = ()


class DecoyState:
    def __init__(self) -> None:
        self._order_matched: list[EventEntry] | None = None
        self._events: list[EventEntry] = []
        self._behaviors: list[BehaviorEntry] = []
        self._behavior_usage_by_index: dict[int, int] = collections.defaultdict(int)
        self._attribute_mocks_by_id: dict[int, object] = {}
        self._matched_event_indices: set[int] = set()
        self._is_paused = False

    def _consume_behavior(
        self,
        event_entry: EventEntry,
    ) -> Behavior | None:
        mock_behaviors = [
            behavior
            for behavior in self._behaviors
            if is_event_from_mock(event_entry, behavior.mock)
        ]
        matched_behaviors = [
            behavior
            for behavior in mock_behaviors
            if is_matching_event(event_entry, behavior.matcher)
        ]

        for behavior_entry in reversed(matched_behaviors):
            usage_count = self._behavior_usage_by_index[behavior_entry.order]

            if is_matching_count(usage_count, behavior_entry.matcher):
                self._behavior_usage_by_index[behavior_entry.order] = usage_count + 1
                self._matched_event_indices.add(event_entry.order)
                return behavior_entry.behavior

        return None

    def _use_behavior(
        self,
        event_entry: EventEntry,
        default_return_value: object = None,
    ) -> object:
        event = event_entry.event
        behavior = self._consume_behavior(event_entry)

        if behavior is None:
            return default_return_value

        if behavior.error:
            raise behavior.error

        elif behavior.action:
            if isinstance(event, CallEvent):
                args = event.args
                kwargs = event.kwargs
            elif isinstance(event, AttributeEvent) and event.value is not MISSING:
                args = (event.value,)
                kwargs = {}
            else:
                args = ()
                kwargs = {}

            return behavior.action(*args, **kwargs)

        elif behavior.context is not MISSING:
            return contextlib.nullcontext(behavior.context)

        return behavior.return_value

    def _add_event(
        self,
        mock: MockInfo,
        event: Event,
        event_state: EventState,
        call_site: CallSite | None = None,
    ) -> EventEntry:
        event_entry = EventEntry(mock, event, event_state, len(self._events), call_site)

        self._events.append(event_entry)

        return event_entry

    def use_call_behavior(
        self,
        mock: MockInfo,
        event: CallEvent,
        event_state: EventState,
        call_site: CallSite | None = None,
    ) -> object:
        event_entry = self._add_event(mock, event, event_state, call_site)

        return self._use_behavior(event_entry)

    def use_attribute_behavior(
        self,
        mock: MockInfo,
        event: AttributeEvent,
        event_state: EventState,
        default_return_value: object = None,
    ) -> object:
        if self._is_paused:
            return default_return_value

        event_entry = self._add_event(mock, event, event_state)

        if (
            event.type == AttributeEventType.GET
            and mock.id in self._attribute_mocks_by_id
        ):
            return self._attribute_mocks_by_id[mock.id]

        if event.type == AttributeEventType.SET:
            self._attribute_mocks_by_id[mock.id] = event.value
        elif event.type == AttributeEventType.DELETE:
            self._attribute_mocks_by_id.pop(mock.id, None)

        return self._use_behavior(event_entry, default_return_value)

    def use_verification(
        self,
        mock: MockInfo,
        matcher: EventMatcher,
    ) -> VerificationResult:
        mock_events = [
            event_entry
            for event_entry in self._events
            if is_verifiable_mock_event(event_entry, mock)
        ]
        all_matching = [
            event_entry
            for event_entry in mock_events
            if is_matching_event(event_entry, matcher)
        ]

        if self._order_matched is not None:
            cursor = self._order_matched[-1].order if self._order_matched else -1
            matching_events = [e for e in all_matching if e.order > cursor]
        else:
            matching_events = all_matching

        is_success = is_successful_verify(
            VerificationEntry(mock, matcher, matching_events)
        )
        is_redundant = is_redundant_verify(
            VerificationEntry(mock, matcher, matching_events), self._behaviors
        )

        self._matched_event_indices.update(e.order for e in matching_events)

        order_anchor: EventEntry | None = None
        order_timeline: tuple[EventEntry, ...] = ()

        if self._order_matched is not None:
            if is_success:
                times = (
                    matcher.options.times if matcher.options.times is not None else 1
                )
                self._order_matched.extend(matching_events[:times])
            elif is_successful_verify(VerificationEntry(mock, matcher, all_matching)):
                order_anchor = self._order_matched[-1]
                involved = {e.mock.id for e in self._order_matched} | {mock.id}
                order_timeline = tuple(e for e in self._events if e.mock.id in involved)

        return VerificationResult(
            is_success=is_success,
            is_redundant=is_redundant,
            mock_events=mock_events,
            matching_events=matching_events,
            order_anchor=order_anchor,
            order_timeline=order_timeline,
        )

    def push_behaviors(
        self,
        mock: MockInfo,
        matcher: EventMatcher,
        behaviors: list[Behavior],
    ) -> None:
        for reversed_index, behavior in enumerate(reversed(behaviors)):
            times = (
                1
                if matcher.options.times is None and reversed_index != 0
                else matcher.options.times
            )
            matcher = EventMatcher(
                event=matcher.event,
                options=matcher.options._replace(times=times),
            )

            self._behaviors.append(
                BehaviorEntry(mock, matcher, behavior, order=len(self._behaviors))
            )

    @contextlib.contextmanager
    def pause(self) -> collections.abc.Generator[None, None, None]:
        previous = self._is_paused
        self._is_paused = True
        yield
        self._is_paused = previous

    @contextlib.contextmanager
    def verify_order(self) -> collections.abc.Generator[None, None, None]:
        previous = self._order_matched
        self._order_matched = []
        try:
            yield
        finally:
            self._order_matched = previous

    def get_miscalled_stubs(self) -> list[MiscalledStub]:
        return [
            MiscalledStub(
                mock_name=entry.mock.name,
                event=entry.event,
                all_events=[
                    e.event
                    for e in self._events
                    if isinstance(e.event, CallEvent)
                    and is_event_from_mock(e, entry.mock)
                ],
                expected_events=[
                    b.matcher.event
                    for b in self._behaviors
                    if is_event_from_mock(entry, b.mock)
                ],
                call_site=entry.call_site,
            )
            for entry in self._events
            if isinstance(entry.event, CallEvent)
            and is_miscalled_stub_event(
                entry,
                self._behaviors,
                self._matched_event_indices,
            )
        ]

    def reset(self) -> None:
        self._events.clear()
        self._behaviors.clear()
        self._behavior_usage_by_index.clear()
        self._attribute_mocks_by_id.clear()
        self._matched_event_indices.clear()
        self._order_matched = None
        self._is_paused = False
