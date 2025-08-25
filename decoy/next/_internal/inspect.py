"""Inspect spec object."""

import collections
import functools
import inspect
from typing import (
    Any,
    Callable,
    Dict,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
    get_type_hints,
)

from ..errors import (
    MockNameRequiredError,
    MockNotAsyncError,
    MockSpecInvalidError,
    SignatureMismatchError,
    ThenDoActionNotCallable,
)

Signature = inspect.Signature


class BoundArguments(NamedTuple):
    """Arguments bound to a spec."""

    args: Tuple[object, ...]
    kwargs: Dict[str, object]


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
    if spec_cls is not None and not inspect.isclass(spec_cls):
        raise MockSpecInvalidError.create("cls")

    if spec_func is not None and not callable(spec_func):
        raise MockSpecInvalidError.create("func")

    return spec_cls or spec_func


def ensure_spec_name(spec: object, fallback_name: Optional[str]) -> str:
    """Get the name of a source object."""
    source_name = getattr(spec, "__name__", None) if spec is not None else None
    name = source_name if isinstance(source_name, str) else fallback_name

    if name is None:
        raise MockNameRequiredError.create()

    return name


def ensure_callable(value: object, is_async: bool) -> Callable[..., object]:
    if not callable(value):
        raise ThenDoActionNotCallable()

    if is_async_callable(value) and not is_async:
        raise MockNotAsyncError()

    return cast(Callable[..., object], value)


def get_spec_module_name(spec: object) -> Optional[str]:
    """Get the name of a source object."""
    module_name = getattr(spec, "__module__", None) if spec is not None else None
    return module_name if isinstance(module_name, str) else None


def get_spec_class_type(spec: object, fallback_type: Type[object]) -> Type[object]:
    return spec if inspect.isclass(spec) else fallback_type


def is_magic_attribute(name: str) -> bool:
    return (
        name.startswith("__")
        and name.endswith("__")
        and name != "__enter__"
        and name != "__exit__"
    )


def get_child_spec(spec: object, child_name: str) -> object:
    if inspect.isclass(spec):
        # inspect object for methods and properties,
        # falling back to type annotations for attributes
        child_hint = _get_type_hints(spec).get(child_name)
        child_source = inspect.getattr_static(spec, child_name, child_hint)

        if isinstance(child_source, property):
            child_source = _get_type_hints(child_source.fget).get("return")

        elif isinstance(child_source, staticmethod):
            child_source = child_source.__func__

        elif isinstance(child_source, classmethod):
            # consume `cls` argument
            child_source = functools.partial(
                child_source.__func__, cast(Type[Any], None)
            )

        elif inspect.isfunction(child_source):
            # consume `self` argument
            child_source = functools.partial(child_source, None)

        return _unwrap_optional(child_source)

    return None


async def get_awaitable_value(value: object) -> object:
    """Get an awaitable value."""
    if inspect.isawaitable(value):
        return await value

    return value


def get_signature(value: object) -> Optional[Signature]:
    """Get the signature of an object, if it's callable."""
    source = _unwrap_callable(value)

    if source is None:
        return None

    try:
        return inspect.signature(source, follow_wrapped=True)
    except (ValueError, TypeError):
        return None


def bind_args(
    signature: Optional[Signature],
    args: Tuple[object, ...],
    kwargs: Dict[str, object],
) -> BoundArguments:
    """Bind given args and kwargs to a signature, if possible."""
    if signature is None:
        return BoundArguments(args, kwargs)

    try:
        bound_args = signature.bind(*args, **kwargs)
    except (TypeError, ValueError) as error:
        raise SignatureMismatchError(error) from None

    return BoundArguments(bound_args.args, bound_args.kwargs)


def _unwrap_callable(value: object) -> Optional[Callable[..., object]]:
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


def _get_type_hints(value: object) -> Dict[str, object]:
    """Get type hints for an object, if possible.

    The builtin `typing.get_type_hints` may fail at runtime,
    e.g. if a type is subscriptable according to mypy but not
    according to Python.
    """
    try:
        return get_type_hints(value)
    except Exception:
        return {}


def _unwrap_optional(value: object) -> object:
    """Return a value's defined type if it's optional.

    If the type is a union of more than just `T | None`,
    bail out and return None to avoid potentially false warnings.
    """
    origin = getattr(value, "__origin__", None)
    args = getattr(value, "__args__", ())

    if origin is not Union or not isinstance(args, collections.abc.Sequence):
        return value

    candidates = [a for a in args if a is not type(None)]

    # TODO(mc, 2025-03-19): support larger unions? might be a lot of work for little payoff
    return candidates[0] if len(candidates) == 1 else None
