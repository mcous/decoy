"""Decoy mocking library.

Use Decoy to create stubs and spies
to isolate your code under test.
"""

from ._internal.decoy import Decoy
from ._internal.mock import AsyncMock, Mock
from ._internal.verify import Verify
from ._internal.when import Stub, When

__all__ = [
    "AsyncMock",
    "Decoy",
    "Mock",
    "Stub",
    "Verify",
    "When",
]
