"""Value objects that move around the mocking system."""

import enum
import inspect
from typing import Callable, NamedTuple, final


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

    args: tuple[object, ...]
    kwargs: dict[str, object]


Event = CallEvent | AttributeEvent


class EventState(NamedTuple):
    is_entered: bool


class MatchOptions(NamedTuple):
    times: int | None
    ignore_extra_args: bool
    is_entered: bool | None


class Behavior(NamedTuple):
    return_value: object = None
    error: Exception | None = None
    action: Callable[..., object] | None = None
    context: object = MISSING


class EventMatcher(NamedTuple):
    event: Event
    options: MatchOptions


class MockInfo(NamedTuple):
    id: int
    name: str
    is_async: bool
    signature: inspect.Signature | None


class CallSite(NamedTuple):
    """Source location of a call to a mock, captured at call time."""

    filename: str
    lineno: int
    module: str


class EventEntry(NamedTuple):
    mock: MockInfo
    event: Event
    state: EventState
    order: int
    call_site: "CallSite | None" = None


class BehaviorEntry(NamedTuple):
    mock: MockInfo
    matcher: EventMatcher
    behavior: Behavior
    order: int


class VerificationEntry(NamedTuple):
    mock: MockInfo
    matcher: EventMatcher
    matching_events: list[EventEntry]


class MiscalledStub(NamedTuple):
    mock_name: str
    event: CallEvent
    expected_events: "list[Event]"
    call_site: "CallSite | None"
