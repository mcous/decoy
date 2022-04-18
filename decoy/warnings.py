"""Warnings raised by Decoy.

See the [warnings guide][] for more details.

[warnings guide]: ../usage/errors-and-warnings/#warnings
"""
import os
from typing import Sequence

from .spy_events import SpyEvent, WhenRehearsal, VerifyRehearsal
from .stringify import stringify_call, stringify_error_message, count


class DecoyWarning(UserWarning):
    """Base class for Decoy warnings."""

    pass


class MiscalledStubWarning(DecoyWarning):
    """A warning when a configured Stub is called with non-matching arguments.

    This warning is raised if a mock is both:

    - Configured as a stub with [`when`][decoy.Decoy.when]
    - Called with arguments that do not match any configured behaviors

    See the [MiscalledStubWarning guide] for more details.

    [MiscalledStubWarning guide]: ../usage/errors-and-warnings/#miscalledstubwarning

    Attributes:
        rehearsals: The mocks's configured rehearsals.
        calls: Actual calls to the mock.
    """

    rehearsals: Sequence[WhenRehearsal]
    calls: Sequence[SpyEvent]

    def __init__(
        self,
        rehearsals: Sequence[WhenRehearsal],
        calls: Sequence[SpyEvent],
    ) -> None:
        heading = os.linesep.join(
            [
                "Stub was called but no matching rehearsal found.",
                f"Found {count(len(rehearsals), 'rehearsal')}:",
            ]
        )

        message = stringify_error_message(
            heading=heading,
            rehearsals=rehearsals,
            calls=calls,
        )

        super().__init__(message)
        self.rehearsals = rehearsals
        self.calls = calls


class RedundantVerifyWarning(DecoyWarning):
    """A warning when a mock is redundantly checked with `verify`.

    A `verify` assertion is redundant if:

    - A given call is used as a [`when`][decoy.Decoy.when] rehearsal
    - That same call is later used in a [`verify`][decoy.Decoy.verify] check

    See the [RedundantVerifyWarning guide][] for more details.

    [RedundantVerifyWarning guide]: ../usage/errors-and-warnings/#redundantverifywarning
    """

    def __init__(self, rehearsal: VerifyRehearsal) -> None:
        message = os.linesep.join(
            [
                "The same rehearsal was used in both a `when` and a `verify`.",
                "This is redundant and probably a misuse of the mock.",
                f"\t{stringify_call(rehearsal)}",
                "See https://mike.cousins.io/decoy/usage/errors-and-warnings/#redundantverifywarning",  # noqa: E501
            ]
        )
        super().__init__(message)
        self.rehearsal = rehearsal


class IncorrectCallWarning(DecoyWarning):
    """A warning raised if a Decoy mock with a spec is called incorrectly.

    If a call to a Decoy mock is incorrect according to `inspect.signature`,
    this warning will be raised.

    See the [IncorrectCallWarning guide][] for more details.

    [IncorrectCallWarning guide]: ../usage/errors-and-warnings/#incorrectcallwarning
    """
