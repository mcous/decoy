"""Spy objects.

Classes in this module are heavily inspired by the
[unittest.mock library](https://docs.python.org/3/library/unittest.mock.html).
"""
from __future__ import annotations
from dataclasses import dataclass
from inspect import isclass, iscoroutinefunction
from typing import get_type_hints, Any, Callable, Dict, Optional, Tuple, Type


@dataclass(frozen=True)
class SpyCall:
    """A dataclass representing a call to a spy.

    Attributes:
        spy_id: Identifier of the spy that made the call
        args: Arguments list of the call
        kwargs: Keyword arguments list of the call
    """

    spy_id: int
    spy_name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    def __str__(self) -> str:
        """Stringify the call to something human readable.

        `SpyCall(spy_id=42, spy_name="name", args=(1,), kwargs={"foo": False})`
        would stringify as `"name(1, foo=False)"`
        """
        args_list = [repr(arg) for arg in self.args]
        kwargs_list = [f"{key}={repr(val)}" for key, val in self.kwargs.items()]

        return f"{self.spy_name}({', '.join(args_list + kwargs_list)})"


CallHandler = Callable[[SpyCall], Any]


class BaseSpy:
    """Spy object base class.

    - Pretends to be another class, if another class is given as a spec
    - Lazily constructs child spies when an attribute is accessed
    """

    def __init__(
        self,
        handle_call: CallHandler,
        spec: Optional[Any] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize a BaseSpy from a call handler and an optional spec object."""
        self._name = name or (spec.__name__ if spec is not None else "spy")
        self._spec = spec
        self._handle_call: CallHandler = handle_call
        self._spy_children: Dict[str, BaseSpy] = {}

    @property  # type: ignore[misc]
    def __class__(self) -> Any:
        """Ensure Spy can pass `instanceof` checks."""
        if isclass(self._spec):
            return self._spec

        return type(self)

    def __getattr__(self, name: str) -> Any:
        """Get a property of the spy.

        Lazily constructs child spies, basing them on type hints if available.
        """
        if name in self._spy_children:
            return self._spy_children[name]

        child_spec = None

        if isclass(self._spec):
            try:
                # NOTE(mc, 2021-01-05): `get_type_hints` may fail at runtime,
                # e.g. if a type is subscriptable according to mypy but not
                # according to Python, `get_type_hints` will raise.
                # Rather than fail to create a spy with an inscrutable error,
                # gracefully fallback to a specification-less spy.
                hints = get_type_hints(self._spec)
                child_spec = getattr(
                    self._spec,
                    name,
                    hints.get(name),
                )
            except Exception:
                pass

        if isinstance(child_spec, property):
            hints = get_type_hints(child_spec.fget)
            child_spec = hints.get("return")

        spy = create_spy(
            handle_call=self._handle_call,
            spec=child_spec,
            name=f"{self._name}.{name}",
        )

        self._spy_children[name] = spy

        return spy


class Spy(BaseSpy):
    """An object that records all calls made to itself and its children."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Handle a call to the spy."""
        return self._handle_call(SpyCall(id(self), self._name, args, kwargs))


class AsyncSpy(BaseSpy):
    """An object that records all async. calls made to itself and its children."""

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Handle a call to the spy asynchronously."""
        return self._handle_call(SpyCall(id(self), self._name, args, kwargs))


def create_spy(
    handle_call: CallHandler,
    spec: Optional[Any] = None,
    is_async: bool = False,
    name: Optional[str] = None,
) -> Any:
    """Create a Spy from a spec.

    Functions and classes passed to `spec` will be inspected (and have any type
    annotations inspected) to ensure `AsyncSpy`'s are returned where necessary.
    """
    _SpyCls: Type[BaseSpy] = Spy

    if iscoroutinefunction(spec) or is_async is True:
        _SpyCls = AsyncSpy

    return _SpyCls(handle_call=handle_call, spec=spec, name=name)
