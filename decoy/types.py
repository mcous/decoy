"""Common type definitions."""
from typing import Any, Callable, TypeVar

FuncT = TypeVar("FuncT", bound=Callable[..., Any])
"""A function to create a decoy of."""

ClassT = TypeVar("ClassT", bound=object)
"""A class to create a decoy of."""

ReturnT = TypeVar("ReturnT")
"""The return type of a given call."""
