"""Common test interfaces."""


class SomeClass:
    """Testing class."""

    def foo(self, val: str) -> str:
        """Get the foo string."""
        ...

    def bar(self, a: int, b: float, c: str) -> bool:
        """Get the bar bool based on a few inputs."""
        ...


def some_func(val: str) -> str:
    """Test function."""
    return "can't touch this"
