"""Spy call verification."""
from typing import Optional, Sequence

from .spy_calls import SpyCall, VerifyRehearsal
from .errors import VerifyError


class Verifier:
    """An interface to verify that spies were called as expected."""

    @staticmethod
    def verify(
        rehearsals: Sequence[VerifyRehearsal],
        calls: Sequence[SpyCall],
        times: Optional[int] = None,
    ) -> None:
        """Verify that a list of calls satisfies a given list of rehearsals."""
        match_count = 0

        for i in range(len(calls)):
            calls_subset = calls[i : i + len(rehearsals)]

            if calls_subset == rehearsals:
                match_count = match_count + 1

        if match_count == 0 or (times is not None and match_count != times):
            raise VerifyError(
                rehearsals=rehearsals,
                calls=calls,
                times=times,
            )
