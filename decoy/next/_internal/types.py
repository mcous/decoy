from typing import Any, Awaitable, Callable, ParamSpec, TypeVar, Union

SpecT = TypeVar("SpecT")
"""The type of a mock spec."""

FuncT = TypeVar("FuncT", bound=Callable[..., Any])
"""A function spec."""

ClassT = TypeVar("ClassT")
"""A class spec."""

ParamsT = ParamSpec("ParamsT")
"""The parameters of a function."""

ReturnT = TypeVar("ReturnT")
"""The return type of a given call."""

ContextValueT = TypeVar("ContextValueT")
"""A context manager value returned by a stub."""

CallableT = Callable[ParamsT, Union[ReturnT, Awaitable[ReturnT]]]
"""A sync or async callable with generic parameters and return value."""
