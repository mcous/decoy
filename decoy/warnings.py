"""Warnings produced by Decoy."""
from os import linesep
from typing import Any, Sequence

from .spy import SpyCall
from .stub import Stub


class MissingStubWarning(UserWarning):
    """A warning raised when a configured stub is called with different arguments."""

    def __init__(self, call: SpyCall, stubs: Sequence[Stub[Any]]) -> None:
        """Initialize the warning message with the actual and expected calls."""
        stubs_len = len(stubs)
        stubs_plural = stubs_len != 1
        stubs_printout = linesep.join(
            [f"{n + 1}.\t{str(stubs[n]._rehearsal)}" for n in range(stubs_len)]
        )

        message = linesep.join(
            [
                "Stub was called but no matching rehearsal found.",
                f"Found {stubs_len} rehearsal{'s' if stubs_plural else ''}:",
                stubs_printout,
                "Actual call:",
                f"\t{str(call)}",
            ]
        )

        super().__init__(message)
