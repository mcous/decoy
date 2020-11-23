"""Decoy and stub configuration registry."""
from mock import Mock
from weakref import finalize, WeakValueDictionary
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .stub import Stub
from .types import Call

if TYPE_CHECKING:
    DecoyMapType = WeakValueDictionary[int, Mock]


class Registry:
    """
    Decoy and stub configuration registry.

    The Registry collects weak-references to decoys created in order to
    automatically clean up stub configurations when a decoy goes out of scope.
    """

    def __init__(self) -> None:
        """Initialize a Registry."""
        self._decoy_map: DecoyMapType = WeakValueDictionary()
        self._stub_map: Dict[int, List[Stub[Any]]] = {}

    def register_decoy(self, decoy: Mock) -> int:
        """Register a decoy for tracking."""
        decoy_id = id(decoy)

        self._decoy_map[decoy_id] = decoy
        finalize(decoy, self._clear_decoy_stubs, decoy_id)

        return decoy_id

    def register_stub(self, decoy_id: int, stub: Stub[Any]) -> None:
        """Register a stub for tracking."""
        stub_list = self.get_decoy_stubs(decoy_id)
        self._stub_map[decoy_id] = stub_list + [stub]

    def get_decoy(self, decoy_id: int) -> Optional[Mock]:
        """Get a decoy by identifier."""
        return self._decoy_map.get(decoy_id)

    def get_decoy_stubs(self, decoy_id: int) -> List[Stub[Any]]:
        """Get a decoy's stub list by identifier."""
        return self._stub_map.get(decoy_id, [])

    def peek_decoy_last_call(self, decoy_id: int) -> Optional[Call]:
        """Get a decoy's last call."""
        decoy = self._decoy_map.get(decoy_id, None)

        if decoy is not None and len(decoy.mock_calls) > 0:
            return decoy.mock_calls[-1]

        return None

    def pop_decoy_last_call(self, decoy_id: int) -> Optional[Call]:
        """Pop a decoy's last call off of its call stack."""
        decoy = self._decoy_map.get(decoy_id, None)

        if decoy is not None and len(decoy.mock_calls) > 0:
            return decoy.mock_calls.pop()

        return None

    def _clear_decoy_stubs(self, decoy_id: int) -> None:
        if decoy_id in self._stub_map:
            del self._stub_map[decoy_id]
