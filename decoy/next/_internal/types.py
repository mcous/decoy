from typing import Any, Callable, ParamSpec, TypeVar

FuncT = TypeVar("FuncT", bound=Callable[..., Any])
"""A function to create a decoy of."""

ClassT = TypeVar("ClassT", bound=object)
"""A class to create a decoy of."""

ParamsT = ParamSpec("ParamsT")
"""The parameters of a function."""

ReturnT = TypeVar("ReturnT")
"""The return type of a given call."""

ContextValueT = TypeVar("ContextValueT")
"""A context manager value returned by a stub."""
