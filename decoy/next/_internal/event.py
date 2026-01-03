import enum
from types import TracebackType
from typing import Callable, Dict, List, NamedTuple, Optional, Tuple, Type, Union, final


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
    value: object = MISSING

    @classmethod
    def get(cls) -> "AttributeEvent":
        return cls(AttributeEventType.GET)

    @classmethod
    def set(cls, value: object) -> "AttributeEvent":
        return cls(AttributeEventType.SET, value)

    @classmethod
    def delete(cls) -> "AttributeEvent":
        return cls(AttributeEventType.DELETE)


class CallEvent(NamedTuple):
    """Event representing a call to a function or method."""

    args: Tuple[object, ...]
    kwargs: Dict[str, object]


class ContextManagerEventType(str, enum.Enum):
    ENTER = "enter"
    EXIT = "exit"


class ContextManagerEvent(NamedTuple):
    """Event representing a context manager enter or exit."""

    type: ContextManagerEventType
    exc_type: Optional[Type[BaseException]]
    exc_value: Optional[BaseException]
    traceback: Optional[TracebackType]

    @classmethod
    def enter(cls) -> "ContextManagerEvent":
        return cls(ContextManagerEventType.ENTER, None, None, None)

    @classmethod
    def exit(
        cls,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> "ContextManagerEvent":
        return cls(ContextManagerEventType.EXIT, exc_type, exc_value, traceback)


Event = Union[CallEvent, AttributeEvent, ContextManagerEvent]


class EventState(NamedTuple):
    is_entered: bool


class EventAndState(NamedTuple):
    event: Event
    event_state: EventState


class MatchOptions(NamedTuple):
    times: Optional[int]
    ignore_extra_args: bool
    is_entered: Optional[bool]


class Behavior(NamedTuple):
    return_value: object = None
    error: Optional[Exception] = None
    action: Optional[Callable[..., object]] = None
    context: object = MISSING


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
        or isinstance(event, (AttributeEvent, ContextManagerEvent))
        or isinstance(expected, (AttributeEvent, ContextManagerEvent))
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
    return (
        match_options.is_entered is None
        or event_state.is_entered == match_options.is_entered
    )
