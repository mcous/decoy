"""Wrappers around contextlib types and fallbacks."""
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    ContextManager,
    Generic,
    TypeVar,
)

# TODO(mc, 2022-03-14): drop support for Python 3.6 in Decoy v2
# Python 3.6 does not have async generator context managers
if TYPE_CHECKING:
    from contextlib import (  # type: ignore[attr-defined]
        _GeneratorContextManager as GeneratorContextManager,
        _AsyncGeneratorContextManager as AsyncGeneratorContextManager,
    )

_EnterT = TypeVar("_EnterT")


class ContextWrapper(
    ContextManager[_EnterT],
    AsyncContextManager[_EnterT],
    Generic[_EnterT],
):
    """A simple, do-nothing ContextManager that wraps a given value.

    Adapted from `contextlib.nullcontext` to ensure support across
    all Python versions.
    """

    def __init__(self, enter_result: _EnterT) -> None:
        self._enter_result = enter_result

    def __enter__(self) -> _EnterT:
        """Return the wrapped value."""
        return self._enter_result

    def __exit__(self, *args: Any, **kwargs: Any) -> Any:
        """No-op on exit."""
        pass

    async def __aenter__(self) -> _EnterT:
        """Return the wrapped value."""
        return self._enter_result

    async def __aexit__(self, *args: Any, **kwargs: Any) -> Any:
        """No-op on exit."""
        pass


__all__ = [
    "AsyncContextManager",
    "AsyncGeneratorContextManager",
    "ContextManager",
    "GeneratorContextManager",
    "ContextWrapper",
]
