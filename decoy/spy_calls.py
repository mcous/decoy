"""Spy call value objects."""
from typing import Any, Dict, NamedTuple, Tuple


class BaseSpyCall(NamedTuple):
    """A value object representing a call to a spy.

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
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    ignore_extra_args: bool = False


class BaseSpyRehearsal(BaseSpyCall):
    """A base class for rehearsals made to `when` or `verify`.

    This base class should not be used directly.
    """

    pass


class SpyCall(BaseSpyCall):
    """An call made to the spy by the code under test."""

    pass


class WhenRehearsal(BaseSpyRehearsal):
    """A call that has been used as a rehearsal for `when`."""

    pass


class VerifyRehearsal(BaseSpyRehearsal):
    """A call that has been used as a rehearsal for `when`."""

    pass


def match_call(call: BaseSpyCall, rehearsal: BaseSpyRehearsal) -> bool:
    """Check if a call matches a given rehearsal."""
    if call.spy_id != rehearsal.spy_id:
        return False

    if rehearsal.ignore_extra_args:
        try:
            args_match = all(
                call.args[i] == value for i, value in enumerate(rehearsal.args)
            )
            kwargs_match = all(
                call.kwargs[key] == value for key, value in rehearsal.kwargs.items()
            )

            return args_match and kwargs_match

        except (IndexError, KeyError):
            return False

    return call.args == rehearsal.args and call.kwargs == rehearsal.kwargs
