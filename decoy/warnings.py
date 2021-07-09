"""Warning value objects."""
import os
from typing import Sequence

from .spy import SpyCall, SpyRehearsal
from .stringify import stringify_error_message, count


class MiscalledStubWarning(UserWarning):
    """A warning when a configured Stub is called with non-matching arguments.

    This warning is raised if a mock is both:

    - Configured as a stub with [`when`][decoy.Decoy.when]
    - Called with arguments that do not match any configured behaviors

    Attributes:
        rehearsals: The mocks's configured rehearsals.
        calls: Actual calls to the mock.
    """

    rehearsals: Sequence[SpyRehearsal]
    calls: Sequence[SpyCall]

    def __init__(
        self,
        rehearsals: Sequence[SpyRehearsal],
        calls: Sequence[SpyCall],
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
