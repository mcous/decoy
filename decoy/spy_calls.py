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
    """

    spy_id: int
    spy_name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]


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
