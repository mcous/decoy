import collections
import collections.abc
import contextlib
import dataclasses
from typing import NamedTuple

from .compare import (
    get_verification_events,
    is_event_from_mock,
    is_matching_behavior,
    is_matching_count,
    is_matching_event,
    is_redundant_verify,
    is_successful_verify,
    is_successful_verify_order,
    is_verifiable_mock_event,
)
from .values import (
    MISSING,
    AttributeEvent,
    AttributeEventType,
    Behavior,
    BehaviorEntry,
    CallEvent,
    Event,
    EventEntry,
    EventMatcher,
    EventState,
    MockInfo,
    VerificationEntry,
)


class BehaviorResult(NamedTuple):
    is_found: bool
    return_value: object
    expected_events: list[Event]


class VerificationResult(NamedTuple):
    is_success: bool
    is_redundant: bool
    matching_events: list[EventEntry]
    mock_events: list[EventEntry]


@dataclasses.dataclass
class OrderVerificationResult:
    is_success: bool = False
    verifications: list[VerificationEntry] = dataclasses.field(default_factory=list)
    all_events: list[EventEntry] = dataclasses.field(default_factory=list)


class DecoyState:
    def __init__(self) -> None:
        self._order_verification: OrderVerificationResult | None = None
        self._events: list[EventEntry] = []
        self._behaviors: list[BehaviorEntry] = []
        self._behavior_usage_by_index: dict[int, int] = collections.defaultdict(int)
        self._attribute_mocks_by_id: dict[int, object] = {}

    def _consume_behavior(
        self,
        event_entry: EventEntry,
    ) -> tuple[Behavior | None, list[Event], bool]:
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
        expected_events = [behavior.matcher.event for behavior in mock_behaviors]

        for behavior_entry in reversed(matched_behaviors):
            usage_count = self._behavior_usage_by_index[behavior_entry.order]

            if is_matching_count(usage_count, behavior_entry.matcher):
                self._behavior_usage_by_index[behavior_entry.order] = usage_count + 1
                return behavior_entry.behavior, expected_events, True

        return None, expected_events, len(matched_behaviors) > 0

    def _use_behavior(
        self,
        event_entry: EventEntry,
        default_return_value: object = None,
    ) -> BehaviorResult:
        event = event_entry.event
        behavior, expected_events, is_found = self._consume_behavior(event_entry)

        if behavior is None:
            return_value = default_return_value

        elif behavior.error:
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

            return_value = behavior.action(*args, **kwargs)

        elif behavior.context is not MISSING:
            return_value = contextlib.nullcontext(behavior.context)

        else:
            return_value = behavior.return_value

        return BehaviorResult(
            is_found=is_found,
            expected_events=expected_events,
            return_value=return_value,
        )

    def _add_event(
        self,
        mock: MockInfo,
        event: Event,
        event_state: EventState,
    ) -> EventEntry:
        event_entry = EventEntry(mock, event, event_state, len(self._events))

        self._events.append(event_entry)

        return event_entry

    def _get_current_attribute_value(self, event_entry: EventEntry) -> object:
        if event_entry.mock.id in self._attribute_mocks_by_id:
            return self._attribute_mocks_by_id[event_entry.mock.id]

        for behavior_entry in reversed(self._behaviors):
            if is_matching_behavior(event_entry, behavior_entry):
                return behavior_entry.behavior.return_value

        return MISSING

    def use_call_behavior(
        self,
        mock: MockInfo,
        event: CallEvent,
        event_state: EventState,
    ) -> BehaviorResult:
        event_entry = self._add_event(mock, event, event_state)
        behavior_result = self._use_behavior(event_entry)

        return behavior_result

    def use_attribute_behavior(
        self,
        mock: MockInfo,
        event: AttributeEvent,
        event_state: EventState,
        default_return_value: object = None,
    ) -> object:
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

        behavior_result = self._use_behavior(event_entry, default_return_value)

        return behavior_result.return_value

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
        matching_events = [
            event_entry
            for event_entry in mock_events
            if is_matching_event(event_entry, matcher)
        ]
        verification = VerificationEntry(mock, matcher, matching_events)
        is_success = is_successful_verify(verification)
        is_redundant = is_redundant_verify(verification, self._behaviors)

        if is_success and self._order_verification:
            self._order_verification.verifications.append(verification)

        return VerificationResult(
            is_success=is_success,
            is_redundant=is_redundant,
            mock_events=mock_events,
            matching_events=matching_events,
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

    def peek_last_attribute_mock(self, value: object) -> MockInfo | None:
        try:
            event_entry = self._events[-1]
        except IndexError:
            return None

        if (
            isinstance(event_entry.event, AttributeEvent)
            and event_entry.event.type == AttributeEventType.GET
            and self._get_current_attribute_value(event_entry) is value
        ):
            return event_entry.mock

        return None

    @contextlib.contextmanager
    def verify_order(self) -> collections.abc.Iterator[OrderVerificationResult]:
        result = OrderVerificationResult(is_success=True)
        self._order_verification = result
        yield result
        self._order_verification = None

        result.all_events = get_verification_events(result.verifications)
        result.is_success = is_successful_verify_order(
            result.verifications,
            result.all_events,
        )

    def reset(self) -> None:
        self._events.clear()
        self._behaviors.clear()
        self._behavior_usage_by_index.clear()
        self._attribute_mocks_by_id.clear()
        self._order_verification = None
