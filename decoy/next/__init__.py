"""Decoy mocking library.

Use Decoy to create stubs and spies
to isolate your code under test.
"""

from ._internal.decoy import AttributeDecoy, Decoy
from ._internal.verify import AttributeVerify, Verify
from ._internal.when import AttributeWhen, SideEffectStub, Stub, When

__all__ = [
    "AttributeDecoy",
    "AttributeVerify",
    "AttributeWhen",
    "Decoy",
    "SideEffectStub",
    "Stub",
    "Verify",
    "When",
]
