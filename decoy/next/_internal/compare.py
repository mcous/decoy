from .values import (
    AttributeEvent,
    AttributeEventType,
    BehaviorEntry,
    CallEvent,
    Event,
    EventEntry,
    EventMatcher,
    EventState,
    MockInfo,
    VerificationEntry,
)


def is_event_from_mock(event_entry: EventEntry, mock: MockInfo) -> bool:
    return mock.id == event_entry.mock.id


def is_verifiable_mock_event(event_entry: EventEntry, mock: MockInfo) -> bool:
    return is_event_from_mock(event_entry, mock) and (
        isinstance(event_entry.event, CallEvent)
        or event_entry.event.type != AttributeEventType.GET
    )


def is_matching_behavior(
    event_entry: EventEntry,
    behavior_entry: BehaviorEntry,
) -> bool:
    return is_event_from_mock(
        event_entry,
        behavior_entry.mock,
    ) and is_matching_event(
        event_entry,
        behavior_entry.matcher,
    )


def is_matching_event(event_entry: EventEntry, matcher: EventMatcher) -> bool:
    event_matches = _match_event(event_entry.event, matcher)
    state_matches = _match_state(event_entry.state, matcher)

    return event_matches and state_matches


def is_matching_count(usage_count: int, matcher: EventMatcher) -> bool:
    return matcher.options.times is None or usage_count < matcher.options.times


def is_successful_verify(verification: VerificationEntry) -> bool:
    if verification.matcher.options.times is not None:
        return len(verification.matching_events) == verification.matcher.options.times

    return len(verification.matching_events) > 0


def get_verification_events(verifications: list[VerificationEntry]) -> list[EventEntry]:
    seen_events: dict[int, bool] = {}
    result: list[EventEntry] = []

    for verification in verifications:
        for matching_event in verification.matching_events:
            if matching_event.order not in seen_events:
                seen_events[matching_event.order] = True
                result.append(matching_event)

    result.sort(key=lambda e: e.order)

    return result


def is_successful_verify_order(
    verifications: list[VerificationEntry],
    events: list[EventEntry],
) -> bool:
    verification_index = 0
    event_index = 0

    while event_index < len(events) and verification_index < len(verifications):
        event = events[event_index]
        verification = verifications[verification_index]
        remaining_events = len(events) - event_index

        if event in verification.matching_events:
            expected_times = verification.matcher.options.times
            verification_index += 1

            if expected_times is None or expected_times == 1:
                event_index += 1
            else:
                for times_index in range(1, expected_times):
                    next_event = events[event_index + times_index]
                    if next_event not in verification.matching_events:
                        return False

                event_index += expected_times

        elif remaining_events >= len(verifications) and verification_index > 0:
            verification_index = 0
        else:
            return False

    return True


def is_redundant_verify(
    verification: VerificationEntry,
    behaviors: list[BehaviorEntry],
) -> bool:
    return any(
        behavior
        for behavior in behaviors
        if verification.mock.id == behavior.mock.id
        and verification.matcher.options == behavior.matcher.options
        and _match_event(verification.matcher.event, behavior.matcher)
    )


def _match_event(event: Event, matcher: EventMatcher) -> bool:
    if (
        matcher.options.ignore_extra_args is False
        or isinstance(event, AttributeEvent)
        or isinstance(matcher.event, AttributeEvent)
    ):
        return event == matcher.event

    try:
        args_match = all(
            value == event.args[i] for i, value in enumerate(matcher.event.args)
        )
        kwargs_match = all(
            value == event.kwargs[key] for key, value in matcher.event.kwargs.items()
        )

        return args_match and kwargs_match

    except (IndexError, KeyError):
        pass

    return False


def _match_state(event_state: EventState, matcher: EventMatcher) -> bool:
    return (
        matcher.options.is_entered is None
        or event_state.is_entered == matcher.options.is_entered
    )
