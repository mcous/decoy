"""Spy call verification."""
from typing import Optional, Sequence

from .spy_events import SpyEvent, VerifyRehearsal, match_event
from .errors import VerifyError

# ensure decoy.verifier does not pollute Pytest tracebacks
__tracebackhide__ = True


class Verifier:
    """An interface to verify that spies were called as expected."""

    @staticmethod
    def verify(
        rehearsals: Sequence[VerifyRehearsal],
        calls: Sequence[SpyEvent],
        times: Optional[int] = None,
    ) -> None:
        """Verify that a list of calls satisfies a given list of rehearsals.

        Arguments:
            rehearsals: Rehearsal calls to verify.
            calls: All calls made to the spies in the rehearsals list.
            times: Number of times the rehearsal sequence should appear in calls.
                If omitted, will look for "at least once."

        Raises:
            VerifyError: the actual calls to the spy did not match the given
                rehearsals.
        """
        match_count = 0

        for i in range(len(calls)):
            calls_subset = calls[i : i + len(rehearsals)]
            matches = [match_event(c, r) for c, r in zip(calls_subset, rehearsals)]

            if all(matches) and len(calls_subset) == len(rehearsals):
                match_count = match_count + 1

        calls_verified = match_count != 0 if times is None else match_count == times

        if not calls_verified:
            raise VerifyError(
                rehearsals=rehearsals,
                calls=calls,
                times=times,
            )
