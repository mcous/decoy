"""Custom unittest.mock subclasses."""

from mock import AsyncMock, MagicMock
from typing import Any, Union


class SyncDecoyMock(MagicMock):
    """MagicMock variant where all child mocks use the parent side_effect."""

    def _get_child_mock(self, **kwargs: Any) -> Any:
        return super()._get_child_mock(**kwargs, side_effect=self.side_effect)


class AsyncDecoyMock(AsyncMock):  # type: ignore[misc]
    """AsyncMock variant where all child mocks use the parent side_effect."""

    def _get_child_mock(self, **kwargs: Any) -> Any:
        return super()._get_child_mock(**kwargs, side_effect=self.side_effect)


DecoyMock = Union[SyncDecoyMock, AsyncDecoyMock]


def create_decoy_mock(is_async: bool, **kwargs: Any) -> DecoyMock:
    """Create a MagicMock or AsyncMock."""
    if is_async is False:
        return SyncDecoyMock(**kwargs)
    else:
        return AsyncDecoyMock(**kwargs)
