"""Spy interaction event value objects."""
import enum
from typing import Any, Dict, NamedTuple, Optional, Tuple, Union


class PropAccessType(str, enum.Enum):
    """Property access type."""

    GET = "get"
    SET = "set"
    DELETE = "delete"


class SpyInfo(NamedTuple):
    """Spy information and configuration."""

    id: int
    name: str
    is_async: bool


class SpyCall(NamedTuple):
    """Spy event payload representing a call to a function or method."""

    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    ignore_extra_args: bool = False


class SpyPropAccess(NamedTuple):
    """Spy event payload representing a get/set/delete of a property."""

    prop_name: str
    access_type: PropAccessType
    value: Optional[Any] = None


class SpyEvent(NamedTuple):
    """An interaction with a spy by the code under test."""

    spy: SpyInfo
    payload: Union[SpyCall, SpyPropAccess]


class WhenRehearsal(NamedTuple):
    """A spy interaction that has been used as a rehearsal for `when`."""

    spy: SpyInfo
    payload: Union[SpyCall, SpyPropAccess]


class VerifyRehearsal(NamedTuple):
    """A spy interaction that has been used as a rehearsal for `verify`."""

    spy: SpyInfo
    payload: Union[SpyCall, SpyPropAccess]


class PropRehearsal(NamedTuple):
    """A spy interaction that has been used as a rehearsal for `prop`."""

    spy: SpyInfo
    payload: SpyPropAccess


SpyRehearsal = Union[WhenRehearsal, VerifyRehearsal, PropRehearsal]

AnySpyEvent = Union[SpyEvent, SpyRehearsal]


def match_event(event: AnySpyEvent, rehearsal: SpyRehearsal) -> bool:
    """Check if a call matches a given rehearsal."""
    if event.spy != rehearsal.spy:
        return False

    if (
        isinstance(event.payload, SpyCall)
        and isinstance(rehearsal.payload, SpyCall)
        and rehearsal.payload.ignore_extra_args
    ):
        call = event.payload
        rehearsed_call = rehearsal.payload

        try:
            args_match = all(
                call.args[i] == value for i, value in enumerate(rehearsed_call.args)
            )
            kwargs_match = all(
                call.kwargs[key] == value
                for key, value in rehearsed_call.kwargs.items()
            )

            return args_match and kwargs_match

        except (IndexError, KeyError):
            return False

    return event.payload == rehearsal.payload
