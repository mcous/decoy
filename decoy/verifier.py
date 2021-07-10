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
        if times is not None:
            if len(calls) == times:
                return None
        else:
            for i, call in enumerate(calls):
                calls_subset = calls[i : i + len(rehearsals)]
                if all(r == calls_subset[j] for j, r in enumerate(rehearsals)):
                    return None

        raise VerifyError(
            rehearsals=rehearsals,
            calls=calls,
            times=times,
        )
