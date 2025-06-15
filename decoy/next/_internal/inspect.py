"""Inspect spec object."""

import functools
import inspect
from typing import Any, Callable, Dict, Optional, Type, cast, get_type_hints

from ..errors import (
    MockNameRequiredError,
    MockNotAsyncError,
    MockSpecInvalidError,
    ThenDoActionNotCallable,
)


def is_async_callable(obj: Any, fallback: bool = False) -> bool:
    """Get whether a spec object is an asynchronous callable."""
    if obj is None:
        return fallback

    source = _unwrap_callable(obj)

    # `iscoroutinefunction` does not work for `partial` on Python < 3.8
    if isinstance(source, functools.partial):
        source = source.func

    return inspect.iscoroutinefunction(source)


def ensure_spec(cls: Any, func: Any) -> Optional[Callable[..., Any]]:
    if cls is not None and not inspect.isclass(cls):
        raise MockSpecInvalidError("cls")

    if func is not None and not callable(func):
        raise MockSpecInvalidError("func")

    return cls or func


def ensure_spec_name(spec: Any, fallback_name: Optional[str]) -> str:
    """Get the name of a source object."""
    source_name = getattr(spec, "__name__", None) if spec is not None else None
    name = source_name if isinstance(source_name, str) else fallback_name

    if name is None:
        raise MockNameRequiredError()

    return name


def ensure_callable(obj: Any) -> Callable[..., Any]:
    if not callable(obj):
        raise ThenDoActionNotCallable()

    return cast(Callable[..., Any], obj)


def ensure_sync_callable(obj: Any) -> Callable[..., Any]:
    verified_callable = ensure_callable(obj)

    if is_async_callable(verified_callable):
        raise MockNotAsyncError()

    return verified_callable


def get_spec_module_name(spec: Any) -> Optional[str]:
    """Get the name of a source object."""
    module_name = getattr(spec, "__module__", None) if spec is not None else None
    return module_name if isinstance(module_name, str) else None


def get_spec_class_type(spec: Any, fallback_type: Type[Any]) -> Type[Any]:
    return spec if inspect.isclass(spec) else fallback_type


def is_magic_attribute(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def get_child_spec(spec: Any, child_name: str) -> Any:
    if inspect.isclass(spec):
        # use type hints to get child spec for class attributes
        return _get_type_hints(spec).get(child_name)


def is_awaitable(obj: Any) -> Any:
    """Get whether an object is awaitable."""
    return inspect.isawaitable(obj)


def _unwrap_callable(obj: Any) -> Any:
    """Return an object's callable, checking if a class has a `__call__` method."""
    # check if spec source is a class with a __call__ method
    if inspect.isclass(obj):
        call_method = inspect.getattr_static(obj, "__call__", None)
        if inspect.isfunction(call_method):
            # consume the `self` argument of the method to ensure proper
            # signature reporting by wrapping it in a partial
            obj = functools.partial(call_method, None)

    return obj


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
