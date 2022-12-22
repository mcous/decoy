"""Core spy logic."""
import inspect
import functools
import warnings
from typing import Any, Dict, NamedTuple, Optional, Tuple, Type, Union, get_type_hints

from .spy_events import SpyInfo
from .warnings import IncorrectCallWarning


class _FROM_SOURCE:
    pass


FROM_SOURCE = _FROM_SOURCE()
"""Indicates a value that should be derived from the source object."""


class BoundArgs(NamedTuple):
    """Arguments bound to a spec."""

    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]


_DEFAULT_SPY_NAME = "unnamed"


class SpyCore:
    """Core spy logic for mimicking a given `source` object.

    Arguments:
        source: The source object the Spy is mimicking.
        name: The spec's name. If `None`, will be derived from `source`.
            Will fallback to a default value.
        module_name: The spec's module name. If left unspecified,
            will be derived from `source`. If explicitly set to `None`,
            a module name will not be used.
        is_async: If the spy should be configured to be an asynchronous callable.
            If `False` or unspecified, will derive from `source`.
    """

    def __init__(
        self,
        source: Optional[object],
        name: Optional[str],
        module_name: Union[str, _FROM_SOURCE, None] = FROM_SOURCE,
        is_async: bool = False,
    ) -> None:
        source = _resolve_source(source)

        self._source = source
        self._name = _get_name(source) if name is None else name
        self._module_name = (
            _get_module_name(source) if module_name is FROM_SOURCE else module_name
        )
        self._full_name = (
            f"{self._module_name}.{self._name}" if self._module_name else self._name
        )
        self._class_type = self._source if inspect.isclass(self._source) else None
        self._signature = _get_signature(source)
        self._is_async = is_async or _get_is_async(source)
        self._info = SpyInfo(id=id(self), name=self._name, is_async=self._is_async)

    @property
    def info(self) -> SpyInfo:
        """Get the spy's information object, for use in SpyLog events."""
        return self._info

    @property
    def full_name(self) -> str:
        """Get the full name of the spy, including module name, if available."""
        return self._full_name

    @property
    def signature(self) -> Optional[inspect.Signature]:
        """Get the spy's signature, if spy represents a callable."""
        return self._signature

    @property
    def class_type(self) -> Optional[Type[Any]]:
        """Get the spy's class type, if spy represents a class."""
        return self._class_type

    @property
    def is_async(self) -> bool:
        """Get whether the spy represents an asynchronous callable."""
        return self._is_async

    def bind_args(self, *args: Any, **kwargs: Any) -> BoundArgs:
        """Bind given args and kwargs to the Spec's signature, if possible.

        If no signature or unable to bind, will simply pass args and kwargs
        through without modification.
        """
        signature = self._signature

        if signature:
            try:
                bound_args = signature.bind(*args, **kwargs)
            except TypeError as e:
                # stacklevel: 4 ensures warning is linked to call location
                warnings.warn(IncorrectCallWarning(e), stacklevel=4)
            else:
                args = bound_args.args
                kwargs = bound_args.kwargs

        return BoundArgs(args=args, kwargs=kwargs)

    def create_child_core(self, name: str, is_async: bool) -> "SpyCore":
        """Create a child attribute, property, or method's SpyCore."""
        source = self._source
        child_name = f"{self._name}.{name}"
        child_source = None

        if inspect.isclass(source):
            # use type hints to get child spec for class attributes
            child_hint = _get_type_hints(source).get(name)
            # use inspect to get child spec for methods and properties
            child_source = inspect.getattr_static(source, name, child_hint)

            if isinstance(child_source, property):
                child_source = _get_type_hints(child_source.fget).get("return")

            elif isinstance(child_source, staticmethod):
                child_source = child_source.__func__

            else:
                if isinstance(child_source, classmethod):
                    child_source = child_source.__func__

                child_source = inspect.unwrap(child_source)

                if inspect.isfunction(child_source):
                    # consume the `self` argument of the method to ensure proper
                    # signature reporting by wrapping it in a partial
                    child_source = functools.partial(child_source, None)

        return SpyCore(
            source=child_source,
            name=child_name,
            module_name=self._module_name,
            is_async=is_async,
        )


def _resolve_source(source: Any) -> Any:
    """Resolve the source object, unwrapping any generic aliases."""
    origin = inspect.getattr_static(source, "__origin__", None)

    return origin if origin is not None else source


def _get_name(source: Any) -> str:
    """Get the name of a source object."""
    source_name = getattr(source, "__name__", None) if source is not None else None
    return source_name if isinstance(source_name, str) else _DEFAULT_SPY_NAME


def _get_module_name(source: Any) -> Optional[str]:
    """Get the name of a source object."""
    module_name = getattr(source, "__module__", None) if source is not None else None
    return module_name if isinstance(module_name, str) else None


def _get_signature(source: Any) -> Optional[inspect.Signature]:
    """Get the signature of a source object."""
    source = _get_callable_source(source)

    try:
        return inspect.signature(source, follow_wrapped=True)
    except (ValueError, TypeError):
        return None


def _get_is_async(source: Any) -> bool:
    """Get whether the source is an asynchronous callable."""
    source = _get_callable_source(source)

    # `iscoroutinefunction` does not work for `partial` on Python < 3.8
    if isinstance(source, functools.partial):
        source = source.func

    return inspect.iscoroutinefunction(source)


def _get_callable_source(source: Any) -> Any:
    """Return the source's callable, checking if a class has a __call__ method."""
    # check if spec source is a class with a __call__ method
    if inspect.isclass(source):
        call_method = inspect.getattr_static(source, "__call__", None)
        if inspect.isfunction(call_method):
            # consume the `self` argument of the method to ensure proper
            # signature reporting by wrapping it in a partial
            source = functools.partial(call_method, None)

    return source


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
