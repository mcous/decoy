from types import TracebackType
from typing import Any, ContextManager, Dict, Optional, Tuple, Type

from ..errors import NotAMockError
from .event import AttributeEvent, CallEvent, EventState
from .inspect import (
    Signature,
    bind_args,
    get_awaitable_value,
    get_child_spec,
    get_signature,
    get_spec_class_type,
    is_async_callable,
    is_magic_attribute,
)
from .state import DecoyState, MockInfo


class MockInternals:
    def __init__(
        self,
        *,
        state: DecoyState,
        spec: object,
        name: str,
        is_async: bool,
        full_name: Optional[str],
        spec_class_type: Type[object],
    ) -> None:
        self.state = state
        self.spec = spec
        self.name = name
        self.full_name = full_name or name
        self.spec_class_type = spec_class_type
        self.children: Dict[str, Mock] = {}
        self.event_state = EventState(is_entered=False)
        self.info = MockInfo(
            id=id(self),
            name=self.full_name,
            is_async=is_async,
            signature=get_signature(spec),
        )

    def call(self, args: Tuple[object, ...], kwargs: Dict[str, object]) -> object:
        bound_args = bind_args(self.info.signature, args, kwargs)
        event = CallEvent(bound_args.args, bound_args.kwargs)

        return self.state.use_behavior(
            mock=self.info,
            event=event,
            event_state=self.event_state,
        )

    def get_child(self, name: str) -> "Mock":
        if name in self.children:
            return self.children[name]

        spec = get_child_spec(self.spec, name)
        child = create_mock(
            spec=spec,
            name=name,
            is_async=is_async_callable(spec),
            parent_name=self.full_name,
            state=self.state,
        )

        self.children[name] = child

        return child


class Mock(ContextManager[Any]):
    _decoy: MockInternals

    def __init__(self, internals: MockInternals) -> None:
        super().__setattr__("_decoy", internals)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._decoy.call(args, kwargs)

    @property  # type: ignore[misc]
    def __class__(self) -> Type[Any]:
        """Ensure mock can pass `isinstance` checks."""
        return self._decoy.spec_class_type

    @property
    def __signature__(self) -> Optional[Signature]:
        """Ensure mock can pass `inspect.signature` checks."""
        return self._decoy.info.signature

    def __repr__(self) -> str:
        return f"<Decoy mock '{self._decoy.full_name}'>"

    def __enter__(self) -> Any:
        self._decoy.event_state = EventState(is_entered=True)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        self._decoy.event_state = EventState(is_entered=False)
        return None

    async def __aenter__(self) -> None:
        self._decoy.event_state = EventState(is_entered=True)

    async def __aexit__(self, *_: object) -> None:
        self._decoy.event_state = EventState(is_entered=False)

    def __getattr__(self, name: str) -> Any:
        if is_magic_attribute(name):
            return super().__getattribute__(name)

        child = self._decoy.get_child(name)

        return self._decoy.state.use_behavior(
            mock=child._decoy.info,
            event=AttributeEvent.get(),
            event_state=self._decoy.event_state,
            default_return_value=child,
        )

    def __setattr__(self, name: str, value: object) -> None:
        child = self._decoy.get_child(name)

        self._decoy.state.use_behavior(
            mock=child._decoy.info,
            event=AttributeEvent.set(value),
            event_state=self._decoy.event_state,
        )

    def __delattr__(self, name: str) -> None:
        child = self._decoy.get_child(name)

        self._decoy.state.use_behavior(
            mock=child._decoy.info,
            event=AttributeEvent.delete(),
            event_state=self._decoy.event_state,
        )


class AsyncMock(Mock):
    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        call_result = self._decoy.call(args, kwargs)
        result = await get_awaitable_value(call_result)

        return result


def create_mock(
    spec: object,
    name: str,
    parent_name: Optional[str],
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


def ensure_mock(method_name: str, maybe_mock: object) -> MockInfo:
    if isinstance(maybe_mock, Mock):
        return maybe_mock._decoy.info

    raise NotAMockError.create(method_name, maybe_mock)
