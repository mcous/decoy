"""Common test fixtures."""
from functools import lru_cache
from typing import Any, Generic, TypeVar, Optional, Union


class SomeClass:
    """Testing class."""

    def foo(self, val: str) -> str:
        """Get the foo string."""
        raise NotImplementedError()

    def bar(self, a: int, b: float, c: str) -> bool:
        """Get the bar bool based on a few inputs."""
        raise NotImplementedError()

    @staticmethod
    def fizzbuzz(hello: str) -> int:
        """Fizz some buzzes."""
        raise NotImplementedError()

    def do_the_thing(self, *, flag: bool) -> None:
        """Perform a side-effect without a return value."""
        raise NotImplementedError()

    @property
    def primitive_property(self) -> str:
        """Get a primitive computed property."""
        raise NotImplementedError()

    @property
    def mystery_property(self):  # type: ignore[no-untyped-def] # noqa: ANN201
        """Get a property without type annotations."""
        raise NotImplementedError()

    @lru_cache(maxsize=None)  # noqa: B019
    def some_wrapped_method(self, val: str) -> str:
        """Get a thing through a wrapped method."""
        raise NotImplementedError()


class SomeNestedClass:
    """Nested testing class."""

    child_attr: SomeClass

    def foo(self, val: str) -> str:
        """Get the foo string."""
        raise NotImplementedError()

    @property
    def child(self) -> SomeClass:
        """Get the child instance."""
        raise NotImplementedError()

    @property
    def optional_child(self) -> Optional[SomeClass]:
        """Get the child instance."""
        raise NotImplementedError()

    @property
    def union_child(self) -> Union[SomeClass, "SomeAsyncClass"]:
        """Get the child instance."""
        raise NotImplementedError()


class SomeAsyncClass:
    """Async testing class."""

    async def foo(self, val: str) -> str:
        """Get the foo string."""
        raise NotImplementedError()

    async def bar(self, a: int, b: float, c: str) -> bool:
        """Get the bar bool based on a few inputs."""
        raise NotImplementedError()

    async def do_the_thing(self, *, flag: bool) -> None:
        """Perform a side-effect without a return value."""
        raise NotImplementedError()

    @classmethod
    async def async_class_method(cls) -> int:
        """Async class method."""
        raise NotImplementedError()

    @staticmethod
    async def async_static_method() -> int:
        """Async static method."""
        raise NotImplementedError()


class SomeAsyncCallableClass:
    """Async callable class."""

    async def __call__(self, val: int) -> int:
        """Get an integer."""
        raise NotImplementedError()


class SomeCallableClass:
    """Async callable class."""

    async def __call__(self, val: int) -> int:
        """Get an integer."""
        raise NotImplementedError()


def noop(*args: Any, **kwargs: Any) -> Any:
    """No-op."""
    raise NotImplementedError()


def some_func(val: str) -> str:
    """Test function."""
    raise NotImplementedError()


async def some_async_func(val: str) -> str:
    """Async test function."""
    raise NotImplementedError()


@lru_cache(maxsize=None)
def some_wrapped_func(val: str) -> str:
    """Test function wrapped in decorator."""
    raise NotImplementedError()


GenericT = TypeVar("GenericT")


class GenericClass(Generic[GenericT]):
    """A generic class definition."""

    def hello(self, val: GenericT) -> None:
        """Say hello."""
        raise NotImplementedError()


ConcreteAlias = GenericClass[str]
"""An alias with a generic type specified"""
