"""Spy objects.

Classes in this module are heavily inspired by the
[unittest.mock library](https://docs.python.org/3/library/unittest.mock.html).
"""
import inspect
from types import TracebackType
from typing import Any, ContextManager, Dict, Optional, Type, Union, cast, overload

from .call_handler import CallHandler
from .spy_core import SpyCore
from .spy_events import SpyCall, SpyEvent, SpyPropAccess, PropAccessType


class BaseSpy(ContextManager[Any]):
    """Spy object base class.

    - Pretends to be another class, if another class is given as a spec
    - Lazily constructs child spies when an attribute is accessed
    """

    _core: SpyCore
    _call_handler: CallHandler
    _spy_creator: "SpyCreator"
    _spy_children: Dict[str, "BaseSpy"]
    _spy_property_values: Dict[str, Any]

    def __init__(
        self,
        core: SpyCore,
        call_handler: CallHandler,
        spy_creator: "SpyCreator",
    ) -> None:
        """Initialize a BaseSpy from a call handler and an optional spec object."""
        super().__setattr__("_decoy_spy_core", core)
        super().__setattr__("_decoy_spy_call_handler", call_handler)
        super().__setattr__("_decoy_spy_creator", spy_creator)
        super().__setattr__("_decoy_spy_children", {})
        super().__setattr__("_decoy_spy_property_values", {})
        super().__setattr__("__signature__", self._decoy_spy_core.signature)

    @property  # type: ignore[misc]
    def __class__(self) -> Any:
        """Ensure Spy can pass `instanceof` checks."""
        return self._decoy_spy_core.class_type or type(self)

    def __enter__(self) -> Any:
        """Allow a spy to be used as a context manager."""
        enter_spy = self._decoy_spy_get_or_create_child_spy("__enter__")
        return enter_spy()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        """Allow a spy to be used as a context manager."""
        exit_spy = self._decoy_spy_get_or_create_child_spy("__exit__")
        return cast(Optional[bool], exit_spy(exc_type, exc_value, traceback))

    async def __aenter__(self) -> Any:
        """Allow a spy to be used as an async context manager."""
        enter_spy = self._decoy_spy_get_or_create_child_spy(
            "__aenter__", child_is_async=True
        )
        return await enter_spy()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        """Allow a spy to be used as a context manager."""
        exit_spy = self._decoy_spy_get_or_create_child_spy(
            "__aexit__", child_is_async=True
        )
        return cast(Optional[bool], await exit_spy(exc_type, exc_value, traceback))

    def __repr__(self) -> str:
        """Get a helpful string representation of the spy."""
        return f"<Decoy mock `{self._decoy_spy_core.full_name}`>"

    def __getattr__(self, name: str) -> Any:
        """Get a property of the spy, always returning a child spy."""
        # do not attempt to mock magic methods
        if name.startswith("__") and name.endswith("__"):
            return super().__getattribute__(name)

        return self._decoy_spy_get_or_create_child_spy(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set a property on the spy, recording the call."""
        event = SpyEvent(
            spy=self._decoy_spy_core.info,
            payload=SpyPropAccess(
                prop_name=name,
                access_type=PropAccessType.SET,
                value=value,
            ),
        )
        self._decoy_spy_call_handler.handle(event)
        self._decoy_spy_property_values[name] = value

    def __delattr__(self, name: str) -> None:
        """Delete a property on the spy, recording the call."""
        event = SpyEvent(
            spy=self._decoy_spy_core.info,
            payload=SpyPropAccess(prop_name=name, access_type=PropAccessType.DELETE),
        )
        self._decoy_spy_call_handler.handle(event)
        self._decoy_spy_property_values.pop(name, None)

    def _decoy_spy_get_or_create_child_spy(
        self, name: str, child_is_async: bool = False
    ) -> Any:
        """Lazily construct a child spy, basing it on type hints if available."""
        # check for any stubbed behaviors for property getter
        get_result = self._decoy_spy_call_handler.handle(
            SpyEvent(
                spy=self._decoy_spy_core.info,
                payload=SpyPropAccess(
                    prop_name=name,
                    access_type=PropAccessType.GET,
                ),
            )
        )

        if get_result:
            return get_result.value

        if name in self._decoy_spy_property_values:
            return self._decoy_spy_property_values[name]

        # return previously constructed (and cached) child spies
        if name in self._decoy_spy_children:
            return self._decoy_spy_children[name]

        child_core = self._decoy_spy_core.create_child_core(
            name=name, is_async=child_is_async
        )
        child_spy = self._decoy_spy_creator.create(core=child_core)
        self._decoy_spy_children[name] = child_spy

        return child_spy

    def _decoy_spy_call(self, *args: Any, **kwargs: Any) -> Any:
        bound_args, bound_kwargs = self._decoy_spy_core.bind_args(*args, **kwargs)
        call = SpyEvent(
            spy=self._decoy_spy_core.info,
            payload=SpyCall(
                args=bound_args,
                kwargs=bound_kwargs,
            ),
        )

        result = self._decoy_spy_call_handler.handle(call)
        return result.value if result else None


class AsyncSpy(BaseSpy):
    """An object that records all async. calls made to itself and its children."""

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Handle a call to the spy asynchronously."""
        result = self._decoy_spy_call(*args, **kwargs)
        return (await result) if inspect.iscoroutine(result) else result


class Spy(BaseSpy):
    """An object that records all calls made to itself and its children."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Handle a call to the spy."""
        return self._decoy_spy_call(*args, **kwargs)


AnySpy = Union[AsyncSpy, Spy]


class SpyCreator:
    """Spy factory."""

    def __init__(self, call_handler: CallHandler) -> None:
        self._decoy_spy_call_handler = call_handler

    @overload
    def create(self, *, core: SpyCore) -> AnySpy:
        ...

    @overload
    def create(
        self, *, spec: Optional[object], name: Optional[str], is_async: bool
    ) -> AnySpy:
        ...

    def create(
        self,
        *,
        core: Optional[SpyCore] = None,
        spec: Optional[object] = None,
        name: Optional[str] = None,
        is_async: bool = False,
    ) -> AnySpy:
        """Create a Spy from a spec.

        Functions and classes passed to `spec` will be inspected (and have any type
        annotations inspected) to ensure `AsyncSpy`'s are returned where necessary.
        """
        if not isinstance(core, SpyCore):
            core = SpyCore(source=spec, name=name, is_async=is_async)

        spy_cls: Type[AnySpy] = AsyncSpy if core.is_async else Spy

        return spy_cls(
            core=core,
            spy_creator=self,
            call_handler=self._decoy_spy_call_handler,
        )
