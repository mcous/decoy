"""Spy objects.

Classes in this module are heavily inspired by the
[unittest.mock library](https://docs.python.org/3/library/unittest.mock.html).
"""
from inspect import getattr_static, isclass, iscoroutinefunction, isfunction, signature
from functools import partial
from warnings import warn
from types import TracebackType
from typing import (
    cast,
    get_type_hints,
    Any,
    Callable,
    ContextManager,
    Dict,
    NamedTuple,
    Optional,
    Type,
)

from .spy_calls import SpyCall
from .warnings import IncorrectCallWarning

CallHandler = Callable[[SpyCall], Any]


class SpyConfig(NamedTuple):
    """Spy configuration options passed to create_spy."""

    handle_call: CallHandler
    spec: Optional[Any] = None
    name: Optional[str] = None
    module_name: Optional[str] = None
    is_async: bool = False


def _get_type_hints(obj: Any) -> Dict[str, Any]:
    """Get type hints for an object, if possible.

    The builtin `typing.get_type_hints` may fail at runtime,
    e.g. if a type is subscriptable according to mypy but not
    according to Python.
    """
    try:
        return get_type_hints(obj)
    except Exception:
        return {}


class BaseSpy(ContextManager[Any]):
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

        self._name = name
        self._module_name = module_name

        if name is None and spec is not None and hasattr(spec, "__name__"):
            self._name = spec.__name__

        if (
            module_name is None
            and spec is not None
            and hasattr(spec, "__module__")
            and not isinstance(spec, partial)
        ):
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

    def __enter__(self) -> Any:
        """Allow a spy to be used as a context manager."""
        enter_spy = self._get_or_create_child_spy("__enter__")
        return enter_spy()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        """Allow a spy to be used as a context manager."""
        exit_spy = self._get_or_create_child_spy("__exit__")
        return cast(Optional[bool], exit_spy(exc_type, exc_value, traceback))

    async def __aenter__(self) -> Any:
        """Allow a spy to be used as an async context manager."""
        enter_spy = self._get_or_create_child_spy("__aenter__")
        return await enter_spy()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        """Allow a spy to be used as a context manager."""
        exit_spy = self._get_or_create_child_spy("__aexit__")
        return cast(Optional[bool], await exit_spy(exc_type, exc_value, traceback))

    def __repr__(self) -> str:
        """Get a helpful string representation of the spy."""
        name = self._name

        if name and self._spec:
            if self._module_name:
                name = f"{self._module_name}.{name}"
            return f"<Decoy mock of {name}>"
        elif name:
            return f'<Decoy mock "{name}">'
        else:
            return "<Decoy mock>"

    def __getattr__(self, name: str) -> Any:
        """Get a property of the spy, always returning a child spy."""
        # do not attempt to mock magic methods
        if name.startswith("__") and name.endswith("__"):
            return super().__getattribute__(name)

        return self._get_or_create_child_spy(name)

    def _get_or_create_child_spy(self, name: str) -> Any:
        """Lazily construct a child spy, basing it on type hints if available."""
        # return previously constructed (and cached) child spies
        if name in self._spy_children:
            return self._spy_children[name]

        child_spec = None
        child_is_async = False
        child_name = f"{self._name}.{name}" if self._name is not None else name

        if isclass(self._spec):
            child_hint = _get_type_hints(self._spec).get(name)
            child_spec = getattr_static(self._spec, name, child_hint)

        if isinstance(child_spec, property):
            child_spec = _get_type_hints(child_spec.fget).get("return")

        if isinstance(child_spec, staticmethod):
            child_spec = child_spec.__func__

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
                name=child_name,
                module_name=self._module_name,
                is_async=child_is_async,
            ),
        )

        self._spy_children[name] = spy

        return spy

    def _call(self, *args: Any, **kwargs: Any) -> Any:
        spy_id = id(self)
        spy_name = (
            self._name
            if self._name
            else f"{type(self).__module__}.{type(self).__qualname__}"
        )

        if hasattr(self, "__signature__"):
            try:
                bound_args = self.__signature__.bind(*args, **kwargs)
            except TypeError as e:
                # stacklevel: 3 ensures warning is linked to call location
                warn(IncorrectCallWarning(e), stacklevel=3)
            else:
                args = bound_args.args
                kwargs = bound_args.kwargs

        return self._handle_call(SpyCall(spy_id, spy_name, args, kwargs))


class Spy(BaseSpy):
    """An object that records all calls made to itself and its children."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Handle a call to the spy."""
        return self._call(*args, **kwargs)


class AsyncSpy(BaseSpy):
    """An object that records all async. calls made to itself and its children."""

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Handle a call to the spy asynchronously."""
        return self._call(*args, **kwargs)


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
