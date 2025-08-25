"""Decoy mocking library.

Use Decoy to create stubs and spies
to isolate your code under test.
"""

from ._internal.decoy import Decoy
from ._internal.verify import Verify
from ._internal.when import EffectsStub, Stub, When

__all__ = ["Decoy", "EffectsStub", "Stub", "Verify", "When"]
