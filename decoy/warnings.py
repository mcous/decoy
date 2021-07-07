"""Warning value objects."""
import textwrap
from typing import Sequence

from .call_stack import SpyCall, SpyRehearsal
from .stringify import stringify_error_message, count


class MiscalledStubWarning(UserWarning):
    """A warning when a configured Stub is called with non-matching arguments.

    This warning is raised if a mock is both:

    - Configured as a stub with [`when`][decoy.Decoy.when]
    - Called with arguments that do not match any configured behaviors
    """

    def __init__(
        self,
        rehearsals: Sequence[SpyRehearsal],
        calls: Sequence[SpyCall],
    ) -> None:
        """Initialize the warning object and its message."""
        heading = textwrap.dedent(
            f"""\
            Stub was called but no matching rehearsal found.
            Found {count(len(rehearsals), 'rehearsal')}:"""
        )

        message = stringify_error_message(
            heading=heading,
            rehearsals=rehearsals,
            calls=calls,
        )

        super().__init__(message)
        self.rehearsals = rehearsals
        self.calls = calls
