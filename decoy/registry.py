"""Decoy and stub registration module."""
from collections import deque
from weakref import finalize
from typing import Any, Deque, Dict, List, Optional

from .spy import BaseSpy, SpyCall
from .stub import Stub


class Registry:
    """Decoy and stub configuration registry.

    The registry collects weak-references to spies and spy calls created in
    order to clean up stub configurations when a spy goes out of scope.
    """

    _calls: Deque[SpyCall]

    def __init__(self) -> None:
        """Initialize a Registry."""
        self._stub_map: Dict[int, List[Stub[Any]]] = {}
        self._calls = deque()

    @property
    def last_call(self) -> Optional[SpyCall]:
        """Peek the last call in the registry's call stack."""
        if len(self._calls) > 0:
            return self._calls[-1]
        else:
            return None

    def pop_last_call(self) -> Optional[SpyCall]:
        """Pop the last call made off the registry's call stack."""
        if len(self._calls) > 0:
            return self._calls.pop()
        else:
            return None

    def get_stubs_by_spy_id(self, spy_id: int) -> List[Stub[Any]]:
        """Get a spy's stub list by identifier.

        Arguments:
            spy_id: The unique identifer of the Spy to look up.

        Returns:
            The list of stubs matching the given Spy.
        """
        return self._stub_map.get(spy_id, [])

    def get_calls_by_spy_id(self, spy_id: int) -> List[SpyCall]:
        """Get a spy's call list by identifier.

        Arguments:
            spy_id: The unique identifer of the Spy to look up.

        Returns:
            The list of calls matching the given Spy.
        """
        return [c for c in self._calls if c.spy_id == spy_id]

    def register_spy(self, spy: BaseSpy) -> int:
        """Register a spy for tracking.

        Arguments:
            spy: The spy to track.

        Returns:
            The spy's unique identifier.
        """
        spy_id = id(spy)
        finalize(spy, self._clear_spy, spy_id)
        return spy_id

    def register_call(self, call: SpyCall) -> None:
        """Register a spy call for tracking.

        Arguments:
            call: The call to track.
        """
        self._calls.append(call)

    def register_stub(self, spy_id: int, stub: Stub[Any]) -> None:
        """Register a stub for tracking.

        Arguments:
            spy_id: The unique identifer of the Spy to look up.
            stub: The stub to track.
        """
        stub_list = self.get_stubs_by_spy_id(spy_id)
        self._stub_map[spy_id] = stub_list + [stub]

    def _clear_spy(self, spy_id: int) -> None:
        """Clear all references to a given spy_id."""
        self._calls = deque([c for c in self._calls if c.spy_id != spy_id])

        if spy_id in self._stub_map:
            del self._stub_map[spy_id]
