import enum
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Union, final


@final
class MISSING:
    """Value not specified sentinel.

    Used when `None` could be a valid value,
    so `Optional` would be inappropriate.
    """


class AttributeEventType(str, enum.Enum):
    GET = "get"
    SET = "set"
    DELETE = "delete"


class AttributeEvent(NamedTuple):
    type: AttributeEventType
    attribute: str
    value: Any = None

    @classmethod
    def get(cls, attribute: str) -> "AttributeEvent":
        return AttributeEvent(AttributeEventType.GET, attribute)

    @classmethod
    def set(cls, attribute: str, value: Any) -> "AttributeEvent":
        return AttributeEvent(AttributeEventType.SET, attribute, value)

    @classmethod
    def delete(cls, attribute: str) -> "AttributeEvent":
        return AttributeEvent(AttributeEventType.DELETE, attribute)


class CallEvent(NamedTuple):
    """Event representing a call to a function or method."""

    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]


Event = Union[CallEvent, AttributeEvent]


class EventState(NamedTuple):
    is_entered: bool


class EventAndState(NamedTuple):
    event: Event
    event_state: EventState


class MatchOptions(NamedTuple):
    times: Optional[int]
    ignore_extra_args: bool
    is_entered: bool


class Behavior(NamedTuple):
    return_value: Optional[Any] = None
    error: Optional[Exception] = None
    action: Optional[Callable[..., Any]] = None
    context: Any = MISSING


def match_event(
    event: Event,
    event_state: EventState,
    expected_event: Event,
    match_options: MatchOptions,
) -> bool:
    """Check if an expected call matches an actual call."""
    event_matches = _match_event(event, expected_event, match_options)
    state_matches = _match_state(event_state, match_options)

    return event_matches and state_matches


def match_event_list(
    events: List[EventAndState],
    expected_event: Event,
    match_options: MatchOptions,
) -> bool:
    match_count = 0

    for event, event_state in events:
        if match_event(event, event_state, expected_event, match_options):
            match_count += 1
            if match_options.times is None:
                return True

    return match_count == match_options.times


def _match_event(event: Event, expected: Event, match_options: MatchOptions) -> bool:
    if (
        match_options.ignore_extra_args is False
        or isinstance(event, AttributeEvent)
        or isinstance(expected, AttributeEvent)
    ):
        return event == expected

    try:
        args_match = all(
            value == event.args[i] for i, value in enumerate(expected.args)
        )
        kwargs_match = all(
            value == event.kwargs[key] for key, value in expected.kwargs.items()
        )

        return args_match and kwargs_match

    except (IndexError, KeyError):
        pass

    return False


def _match_state(event_state: EventState, match_options: MatchOptions) -> bool:
    return event_state.is_entered == match_options.is_entered
