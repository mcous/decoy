"""Common test interfaces."""
from typing import Any


class SomeClass:
    """Testing class."""

    def foo(self, val: str) -> str:
        """Get the foo string."""
        ...

    def bar(self, a: int, b: float, c: str) -> bool:
        """Get the bar bool based on a few inputs."""
        ...

    @staticmethod
    def fizzbuzz(hello: str) -> int:
        """Fizz some buzzes."""
        ...

    def do_the_thing(self, *, flag: bool) -> None:
        """Perform a side-effect without a return value."""
        ...

    @property
    def primitive_property(self) -> str:
        """Get a primitive computed property."""
        ...


class SomeNestedClass:
    """Nested testing class."""

    child_attr: SomeClass

    def foo(self, val: str) -> str:
        """Get the foo string."""
        ...

    @property
    def child(self) -> SomeClass:
        """Get the child instance."""
        ...


class SomeAsyncClass:
    """Async testing class."""

    async def foo(self, val: str) -> str:
        """Get the foo string."""
        ...

    async def bar(self, a: int, b: float, c: str) -> bool:
        """Get the bar bool based on a few inputs."""
        ...

    async def do_the_thing(self, *, flag: bool) -> None:
        """Perform a side-effect without a return value."""
        ...


class SomeAsyncCallableClass:
    """Async callable class."""

    async def __call__(self, val: int) -> int:
        """Get an integer."""
        ...


class SomeCallableClass:
    """Async callable class."""

    async def __call__(self, val: int) -> int:
        """Get an integer."""
        ...


# NOTE: these `Any`s are forward references for call signature testing purposes
def noop(*args: Any, **kwargs: Any) -> Any:
    """No-op."""
    pass


def some_func(val: str) -> str:
    """Test function."""
    return "can't touch this"


async def some_async_func(val: str) -> str:
    """Async test function."""
    return "can't touch this"
