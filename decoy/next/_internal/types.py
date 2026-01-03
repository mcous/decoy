from typing import (
    Any,
    Awaitable,
    Callable,
    ContextManager,
    ParamSpec,
    Protocol,
    TypeVar,
    Union,
)

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


class CallableContextManager(Protocol[ContextValueT, ParamsT, ReturnT]):
    def __call__(
        self, *args: ParamsT.args, **kwargs: ParamsT.kwargs
    ) -> Union[ReturnT, Awaitable[ReturnT]]: ...

    def __enter__(self) -> ContextValueT: ...


MockT = Union[
    CallableContextManager[ContextValueT, ParamsT, ReturnT],
    ContextManager[ContextValueT],
    Callable[ParamsT, ReturnT],
]
"""Mock types, to extract paramters, return types, and context manager values"""
