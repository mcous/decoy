import inspect
import warnings
from types import TracebackType
from typing import Any, cast

from .inspect import (
    bind_args,
    get_awaitable_value,
    get_child_spec,
    get_method_class,
    get_signature,
    get_spec_class_type,
    is_async_callable,
    is_magic_attribute,
)
from .state import DecoyState
from .values import AttributeEvent, CallEvent, EventState, MockInfo
from .warnings import createMiscalledStubWarning


class MockInternals:
    def __init__(
        self,
        *,
        state: DecoyState,
        spec: object,
        name: str,
        is_async: bool,
        full_name: str | None,
        spec_class_type: type[object],
    ) -> None:
        self.state = state
        self.spec = spec
        self.name = name
        self.full_name = full_name or name
        self.spec_class_type = spec_class_type
        self.children: dict[str, Mock] = {}
        self.attribute_values: dict[str, object] = {}
        self.event_state = EventState(is_entered=False)
        self.info = MockInfo(
            id=id(self),
            name=self.full_name,
            is_async=is_async,
            signature=get_signature(spec),
        )

    def call(self, args: tuple[object, ...], kwargs: dict[str, object]) -> object:
        bound_args = bind_args(self.info.signature, args, kwargs)
        event = CallEvent(bound_args.args, bound_args.kwargs)
        behavior = self.state.use_call_behavior(
            mock=self.info,
            event=event,
            event_state=self.event_state,
        )

        if not behavior.is_found and behavior.expected_events:
            warnings.warn(
                createMiscalledStubWarning(
                    self.name,
                    behavior.expected_events,
                    event,
                ),
                stacklevel=3,
            )

        return behavior.return_value

    def get_child(self, name: str, is_async: bool = False) -> "Mock":
        if name in self.children:
            return self.children[name]

        spec = get_child_spec(self.spec, name)
        child = create_mock(
            spec=spec,
            name=name,
            is_async=is_async_callable(spec) if spec else is_async,
            parent_name=self.full_name,
            state=self.state,
        )

        self.children[name] = child

        return child


class Mock:
    """A mock callable/class, created by [`Decoy.mock`][decoy.next.Decoy.mock]."""

    _decoy: MockInternals

    def __init__(self, internals: MockInternals) -> None:
        super().__setattr__("_decoy", internals)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._decoy.call(args, kwargs)

    @property  # type: ignore[misc]
    def __class__(self) -> type[Any]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Imitate `isinstance` checks."""
        return self._decoy.spec_class_type

    @property
    def __signature__(self) -> inspect.Signature | None:
        """Imitate `inspect.signature` checks."""
        return self._decoy.info.signature

    def __repr__(self) -> str:
        return f"<Decoy mock `{self._decoy.full_name}`>"

    def __enter__(self) -> Any:
        enter = self._decoy.get_child("__enter__")
        self._decoy.event_state = EventState(is_entered=True)

        return enter()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        exit = self._decoy.get_child("__exit__")
        self._decoy.event_state = EventState(is_entered=False)

        return cast(bool | None, exit(exc_type, exc_value, traceback))

    async def __aenter__(self) -> Any:
        enter = self._decoy.get_child("__aenter__", is_async=True)
        self._decoy.event_state = EventState(is_entered=True)

        return await enter()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        exit = self._decoy.get_child("__aexit__", is_async=True)
        self._decoy.event_state = EventState(is_entered=False)

        return cast(bool | None, await exit(exc_type, exc_value, traceback))

    def __getattr__(self, name: str) -> Any:
        if is_magic_attribute(name):
            return super().__getattribute__(name)

        child = self._decoy.get_child(name)

        return self._decoy.state.use_attribute_behavior(
            mock=child._decoy.info,
            event=AttributeEvent.get(),
            event_state=self._decoy.event_state,
            default_return_value=child,
        )

    def __setattr__(self, name: str, value: object) -> None:
        child = self._decoy.get_child(name)

        self._decoy.state.use_attribute_behavior(
            mock=child._decoy.info,
            event=AttributeEvent.set(value),
            event_state=self._decoy.event_state,
        )

    def __delattr__(self, name: str) -> None:
        child = self._decoy.get_child(name)

        self._decoy.state.use_attribute_behavior(
            mock=child._decoy.info,
            event=AttributeEvent.delete(),
            event_state=self._decoy.event_state,
        )


class AsyncMock(Mock):
    """A mock async callable/class, created by [`Decoy.mock`][decoy.next.Decoy.mock]."""

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        call_result = self._decoy.call(args, kwargs)
        result = await get_awaitable_value(call_result)

        return result


def create_mock(
    spec: object,
    name: str,
    parent_name: str | None,
    is_async: bool,
    state: DecoyState,
) -> Mock:
    cls = AsyncMock if is_async else Mock
    mock_internals = MockInternals(
        state=state,
        spec=spec,
        name=name,
        is_async=is_async,
        full_name=name if parent_name is None else f"{parent_name}.{name}",
        spec_class_type=get_spec_class_type(spec, cls),
    )

    return cls(mock_internals)


def ensure_mock(maybe_mock: object) -> MockInfo | None:
    if isinstance(maybe_mock, Mock):
        return maybe_mock._decoy.info

    for cm_method, is_async in (
        ("__enter__", False),
        ("__exit__", False),
        ("__aenter__", True),
        ("__aexit__", True),
    ):
        maybe_cm_mock = get_method_class(cm_method, maybe_mock)
        if isinstance(maybe_cm_mock, Mock):
            return maybe_cm_mock._decoy.get_child(cm_method, is_async)._decoy.info

    return None
