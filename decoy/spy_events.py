"""Spy interaction event value objects."""
import enum
from typing import Any, Dict, NamedTuple, Optional, Tuple, Union


class PropAccessType(str, enum.Enum):
    """Property access type."""

    GET = "get"
    SET = "set"
    DELETE = "delete"


class SpyCall(NamedTuple):
    """Spy event payload representing a call to a function or method."""

    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    ignore_extra_args: bool = False


class SpyPropAccess(NamedTuple):
    """Spy event payload representing a get/set/delete of a property."""

    access_type: PropAccessType
    prop_name: str
    value: Optional[Any] = None


class BaseSpyEvent(NamedTuple):
    """A value object representing an interaction event with a spy.

    This base class should not be used directly.

    Attributes:
        spy_id: Identifier of the spy that made the call.
        spy_name: String name of the spy.
        args: Arguments list of the call.
        kwargs: Keyword arguments list of the call.
        ignore_extra_args: Whether extra arguments to the call should
            be ignored during comparison. Only used by rehearsals.
    """

    spy_id: int
    spy_name: str
    payload: Union[SpyCall, SpyPropAccess]


class SpyEvent(BaseSpyEvent):
    """An interaction with a spy by the code under test."""


class BaseSpyRehearsal(BaseSpyEvent):
    """A base class for rehearsals made to `when` or `verify`."""


class WhenRehearsal(BaseSpyRehearsal):
    """A spy interaction that has been used as a rehearsal for `when`."""


class VerifyRehearsal(BaseSpyRehearsal):
    """A spy interaction that has been used as a rehearsal for `verify`."""


def match_event(event: BaseSpyEvent, rehearsal: BaseSpyRehearsal) -> bool:
    """Check if a call matches a given rehearsal."""
    if event.spy_id != rehearsal.spy_id:
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
