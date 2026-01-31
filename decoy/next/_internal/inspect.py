"""Inspect spec object."""

import functools
import inspect
from typing import (
    Callable,
    NamedTuple,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from .errors import (
    createMockNameRequiredError,
    createMockNotAsyncError,
    createMockSpecInvalidError,
    createSignatureMismatchError,
    createThenDoActionNotCallableError,
)


class BoundArguments(NamedTuple):
    """Arguments bound to a spec."""

    args: tuple[object, ...]
    kwargs: dict[str, object]


def is_async_callable(value: object, fallback: bool = False) -> bool:
    """Get whether a spec object is an asynchronous callable."""
    if value is None:
        return fallback

    source = _unwrap_callable(value)

    # `iscoroutinefunction` does not work for `partial` on Python < 3.8
    if isinstance(source, functools.partial):
        source = source.func

    return inspect.iscoroutinefunction(_unwrap_callable(value))


def ensure_spec(spec_cls: object, spec_func: object) -> object:
    spec_cls = _unwrap_type_alias(spec_cls)

    if spec_cls is not None and not inspect.isclass(spec_cls):
        raise createMockSpecInvalidError("cls")

    if spec_func is not None and not callable(spec_func):
        raise createMockSpecInvalidError("func")

    return spec_cls or spec_func


def ensure_spec_name(spec: object, fallback_name: str | None) -> str:
    """Get the name of a source object."""
    source_name = getattr(spec, "__name__", None) if spec is not None else None
    name = source_name if isinstance(source_name, str) else fallback_name

    if name is None:
        raise createMockNameRequiredError()

    return name


def ensure_callable(value: object, is_async: bool) -> Callable[..., object]:
    if not callable(value):
        raise createThenDoActionNotCallableError()

    if is_async_callable(value) and not is_async:
        raise createMockNotAsyncError()

    return cast(Callable[..., object], value)


def get_spec_module_name(spec: object) -> str | None:
    """Get the name of a source object."""
    module_name = getattr(spec, "__module__", None) if spec is not None else None
    return module_name if isinstance(module_name, str) else None


def get_spec_class_type(spec: object, fallback_type: type[object]) -> type[object]:
    return spec if inspect.isclass(spec) else fallback_type


def is_magic_attribute(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def get_child_spec(spec: object, child_name: str) -> object:
    if inspect.isclass(spec):
        # inspect object for methods and properties,
        # falling back to type annotations for attributes
        child_hint = _get_type_hints(spec).get(child_name)
        child_source = inspect.getattr_static(spec, child_name, child_hint)
        unwrapped_child_source = inspect.unwrap(child_source)

        if isinstance(child_source, staticmethod):
            return unwrapped_child_source

        if isinstance(unwrapped_child_source, property):
            return _unwrap_type_alias(
                _get_type_hints(unwrapped_child_source.fget).get("return")
            )

        if inspect.isfunction(unwrapped_child_source):
            # consume `self` argument
            return functools.partial(unwrapped_child_source, None)

        return _unwrap_type_alias(unwrapped_child_source)

    return None


def get_method_class(name: str, maybe_method: object) -> object:
    if inspect.ismethod(maybe_method) and maybe_method.__name__ == name:
        return maybe_method.__self__

    return None


async def get_awaitable_value(value: object) -> object:
    """Get an awaitable value."""
    if inspect.isawaitable(value):
        return await value

    return value


def get_signature(value: object) -> inspect.Signature | None:
    """Get the signature of an object, if it's callable."""
    source = _unwrap_callable(value)

    if source is None:
        return None

    try:
        return inspect.signature(source, follow_wrapped=True)
    except (ValueError, TypeError):
        return None


def bind_args(
    signature: inspect.Signature | None,
    args: tuple[object, ...],
    kwargs: dict[str, object],
    ignore_extra_args: bool = False,
) -> BoundArguments:
    """Bind given args and kwargs to a signature, if possible."""
    if signature is None:
        return BoundArguments(args, kwargs)

    try:
        if ignore_extra_args:
            bound_args = signature.bind_partial(*args, **kwargs)
        else:
            bound_args = signature.bind(*args, **kwargs)
    except (TypeError, ValueError) as error:
        raise createSignatureMismatchError(error) from None

    return BoundArguments(bound_args.args, bound_args.kwargs)


def _unwrap_callable(value: object) -> Callable[..., object] | None:
    """Return an object's callable, checking if a class has a `__call__` method."""
    if not callable(value):
        return None

    # check if spec source is a class with a __call__ method
    if inspect.isclass(value):
        call_method = inspect.getattr_static(value, "__call__", None)
        if inspect.isfunction(call_method):
            # consume the `self` argument of the method to ensure proper
            # signature reporting by wrapping it in a partial
            value = functools.partial(call_method, None)

    return value


def _get_type_hints(value: object) -> dict[str, object]:
    """Get type hints for an object, if possible.

    The builtin `typing.get_type_hints` may fail at runtime,
    e.g. if a type is subscriptable according to mypy but not
    according to Python.
    """
    try:
        return get_type_hints(value)
    except Exception:
        return {}


def _unwrap_type_alias(value: object) -> object:
    """Return a value's actual type if it's a type alias.

    If the resolved origin is a `Union`, remove any `None` values
    to see if we can resolve to an individual specific type.

    If we cannot resolve to a specific type, return the original value.
    """
    origin = _resolve_origin(value)
    type_args = get_args(value)

    if origin is not Union:
        return origin

    candidates = [a for a in type_args if a is not type(None)]

    return candidates[0] if len(candidates) == 1 else origin


def _resolve_origin(source: object) -> object:
    """Resolve the origin of an object.

    This allows a type alias to be used as a class spec.
    """
    origin = get_origin(source)

    return origin if origin is not None else source
