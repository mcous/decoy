"""Mock specification."""
import inspect
import functools
import warnings
from typing import Any, Dict, NamedTuple, Optional, Tuple, Type, Union, get_type_hints

from .warnings import IncorrectCallWarning


class BoundArgs(NamedTuple):
    """Arguments bound to a spec."""

    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]


class Spec:
    """Interface defining a Spy's specification.

    Arguments:
        source: The source object for the specification.
        name: The spec's name. If left unspecified, will be derived from
            `source`, if possible. Will fallback to a default value.
        module_name: The spec's module name. If left unspecified or `True`,
            will be derived from `source`, if possible. If explicitly set to `None`
            or `False` or it is unable to be derived, a module name will not be used.

    """

    _DEFAULT_SPY_NAME = "unnamed"

    def __init__(
        self,
        source: Optional[Any],
        name: Optional[str],
        module_name: Union[str, bool, None] = True,
    ) -> None:
        self._source = source

        if name is not None:
            self._name = name
        elif source is not None:
            self._name = getattr(source, "__name__", self._DEFAULT_SPY_NAME)
        else:
            self._name = self._DEFAULT_SPY_NAME

        if isinstance(module_name, str):
            self._module_name: Optional[str] = module_name
        elif module_name is True and source is not None:
            self._module_name = getattr(source, "__module__", None)
        else:
            self._module_name = None

    def get_name(self) -> str:
        """Get the Spec's human readable name.

        Name may be manually specified or derived from the object the Spec
        represents.
        """
        return self._name

    def get_full_name(self) -> str:
        """Get the full name of the spec.

        Full name includes the module name of the object the Spec represents,
        if available.
        """
        name = self._name
        module_name = self._module_name
        return f"{module_name}.{name}" if module_name else name

    def get_signature(self) -> Optional[inspect.Signature]:
        """Get the Spec's signature, if Spec represents a callable."""
        source = self._get_source()

        try:
            return inspect.signature(source)
        except TypeError:
            return None

    def get_class_type(self) -> Optional[Type[Any]]:
        """Get the Spec's class type, if Spec represents a class."""
        return self._source if inspect.isclass(self._source) else None

    def get_is_async(self) -> bool:
        """Get whether the Spec represents an async. callable."""
        source = self._get_source()

        # `iscoroutinefunction` does not work for `partial` on Python < 3.8
        if isinstance(source, functools.partial):
            source = source.func

        return inspect.iscoroutinefunction(source)

    def bind_args(self, *args: Any, **kwargs: Any) -> BoundArgs:
        """Bind given args and kwargs to the Spec's signature, if possible.

        If no signature or unable to bind, will simply pass args and kwargs
        through without modification.
        """
        signature = self.get_signature()

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

    def get_child_spec(self, name: str) -> "Spec":
        """Get a child attribute, property, or method's Spec from this Spec."""
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

            elif inspect.isfunction(child_source):
                # consume the `self` argument of the method to ensure proper
                # signature reporting by wrapping it in a partial
                child_source = functools.partial(child_source, None)

        return Spec(source=child_source, name=child_name, module_name=self._module_name)

    def _get_source(self) -> Any:
        source = self._source

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
