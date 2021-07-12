"""Spy objects.

Classes in this module are heavily inspired by the
[unittest.mock library](https://docs.python.org/3/library/unittest.mock.html).
"""
from inspect import isclass, iscoroutinefunction, isfunction, signature
from functools import partial
from typing import get_type_hints, Any, Callable, Dict, NamedTuple, Optional

from .spy_calls import SpyCall


CallHandler = Callable[[SpyCall], Any]


class SpyConfig(NamedTuple):
    """Spy configuration options passed to create_spy."""

    handle_call: CallHandler
    spec: Optional[Any] = None
    name: Optional[str] = None
    module_name: Optional[str] = None
    is_async: bool = False


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
        module_name: Optional[str] = None,
    ) -> None:
        """Initialize a BaseSpy from a call handler and an optional spec object."""
        self._spec = spec
        self._handle_call: CallHandler = handle_call
        self._spy_children: Dict[str, BaseSpy] = {}

        self._name = name or (spec.__name__ if spec is not None else "spy")
        self._module_name = module_name

        if module_name is None and spec is not None and hasattr(spec, "__module__"):
            self._module_name = spec.__module__

        # ensure spy can pass inspect.signature checks
        try:
            self.__signature__ = signature(spec)  # type: ignore[arg-type]
        except Exception:
            pass

    @property  # type: ignore[misc]
    def __class__(self) -> Any:
        """Ensure Spy can pass `instanceof` checks."""
        if isclass(self._spec):
            return self._spec

        return type(self)

    def __repr__(self) -> str:
        """Get a helpful string representation of the spy."""
        name = self._name
        if self._module_name:
            name = f"{self._module_name}.{name}"

        return f"<Decoy mock of {name}>" if self._spec else "<Decoy spy function>"

    def __getattr__(self, name: str) -> Any:
        """Get a property of the spy.

        Lazily constructs child spies, basing them on type hints if available.
        """
        # do not attempt to mock magic methods
        if name.startswith("__") and name.endswith("__"):
            return super().__getattribute__(name)

        # return previously constructed (and cached) child spies
        if name in self._spy_children:
            return self._spy_children[name]

        child_spec = None
        child_is_async = False

        if isclass(self._spec):
            try:
                # NOTE: `get_type_hints` may fail at runtime,
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
        elif isclass(self._spec) and isfunction(child_spec):
            # `iscoroutinefunction` does not work for `partial` on Python < 3.8
            # check before we wrap it
            child_is_async = iscoroutinefunction(child_spec)
            # consume the `self` argument of the method to ensure proper
            # signature reporting by wrapping it in a partial
            child_spec = partial(child_spec, None)  # type: ignore[arg-type]

        spy = create_spy(
            config=SpyConfig(
                handle_call=self._handle_call,
                spec=child_spec,
                name=f"{self._name}.{name}",
                module_name=self._module_name,
                is_async=child_is_async,
            ),
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


SpyFactory = Callable[[SpyConfig], Any]


def create_spy(config: SpyConfig) -> Any:
    """Create a Spy from a spec.

    Functions and classes passed to `spec` will be inspected (and have any type
    annotations inspected) to ensure `AsyncSpy`'s are returned where necessary.
    """
    handle_call, spec, name, module_name, is_async = config
    _SpyCls = AsyncSpy if iscoroutinefunction(spec) or is_async is True else Spy

    return _SpyCls(
        handle_call=handle_call,
        spec=spec,
        name=name,
        module_name=module_name,
    )
