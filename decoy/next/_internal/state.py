import collections
import collections.abc
import contextlib
import dataclasses
from typing import NamedTuple

from .match import (
    is_event_from_mock,
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
    is_success: bool
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
        self.is_verifying_attributes = False
        self._order_verification: OrderVerificationResult | None = None
        self._events: list[EventEntry] = []
        self._behaviors: list[BehaviorEntry] = []
        self._behavior_usage_by_index: dict[int, int] = collections.defaultdict(int)

    def _consume_behavior(
        self,
        matched_behaviors: list[BehaviorEntry],
    ) -> Behavior | None:
        for behavior_entry in reversed(matched_behaviors):
            usage_count = self._behavior_usage_by_index[behavior_entry.order]

            if is_matching_count(usage_count, behavior_entry.matcher):
                self._behavior_usage_by_index[behavior_entry.order] = usage_count + 1
                return behavior_entry.behavior

        return None

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

    def use_behavior(
        self,
        *,
        mock: MockInfo,
        event: Event,
        event_state: EventState,
        default_return_value: object = None,
    ) -> BehaviorResult:
        event_entry = EventEntry(mock, event, event_state, len(self._events))
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
        behavior = self._consume_behavior(matched_behaviors)

        self._events.append(event_entry)

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
            is_success=len(matched_behaviors) > 0,
            expected_events=[behavior.matcher.event for behavior in mock_behaviors],
            return_value=return_value,
        )

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

    @contextlib.contextmanager
    def verify_attributes(self) -> collections.abc.Iterator[None]:
        self.is_verifying_attributes = True
        yield
        self.is_verifying_attributes = False

    @contextlib.contextmanager
    def verify_order(self) -> collections.abc.Iterator[OrderVerificationResult]:
        result = OrderVerificationResult(is_success=True)
        self._order_verification = result
        yield result
        self._order_verification = None

        for verification in result.verifications:
            result.all_events.extend(verification.matching_events)

        result.all_events.sort(key=lambda event: event.order)
        result.is_success = is_successful_verify_order(result.verifications)

    def reset(self) -> None:
        self.is_verifying_attributes = False
        self._events.clear()
        self._behaviors.clear()
        self._behavior_usage_by_index.clear()
        self._order_verification = None
