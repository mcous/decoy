"""Common test fixtures."""
from functools import lru_cache
from typing import Any, Generic, TypeVar


class SomeClass:
    """Testing class."""

    def foo(self, val: str) -> str:
        """Get the foo string."""

    def bar(self, a: int, b: float, c: str) -> bool:
        """Get the bar bool based on a few inputs."""

    @staticmethod
    def fizzbuzz(hello: str) -> int:
        """Fizz some buzzes."""

    def do_the_thing(self, *, flag: bool) -> None:
        """Perform a side-effect without a return value."""

    @property
    def primitive_property(self) -> str:
        """Get a primitive computed property."""

    @lru_cache(maxsize=None)
    def some_wrapped_method(self, val: str) -> str:
        """Get a thing through a wrapped method."""


class SomeNestedClass:
    """Nested testing class."""

    child_attr: SomeClass

    def foo(self, val: str) -> str:
        """Get the foo string."""

    @property
    def child(self) -> SomeClass:
        """Get the child instance."""


class SomeAsyncClass:
    """Async testing class."""

    async def foo(self, val: str) -> str:
        """Get the foo string."""

    async def bar(self, a: int, b: float, c: str) -> bool:
        """Get the bar bool based on a few inputs."""

    async def do_the_thing(self, *, flag: bool) -> None:
        """Perform a side-effect without a return value."""

    @classmethod
    async def async_class_method(cls) -> int:
        """An async class method."""

    @staticmethod
    async def async_static_method() -> int:
        """An async static method."""


class SomeAsyncCallableClass:
    """Async callable class."""

    async def __call__(self, val: int) -> int:
        """Get an integer."""


class SomeCallableClass:
    """Async callable class."""

    async def __call__(self, val: int) -> int:
        """Get an integer."""


def noop(*args: Any, **kwargs: Any) -> Any:
    """No-op."""


def some_func(val: str) -> str:
    """Test function."""


async def some_async_func(val: str) -> str:
    """Async test function."""


@lru_cache(maxsize=None)
def some_wrapped_func(val: str) -> str:
    """Wrapped test function."""


GenericT = TypeVar("GenericT")


class GenericClass(Generic[GenericT]):
    """A generic class definition."""

    def hello(self, val: GenericT) -> None:
        """Say hello."""


ConcreteAlias = GenericClass[str]
"""An alias with a generic type specified"""
