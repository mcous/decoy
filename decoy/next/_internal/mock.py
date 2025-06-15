import contextlib
from typing import Any, Dict, Optional, Set, Tuple, Type

from ..errors import NotAMockError
from .event import MISSING, AttributeEvent, Behavior, CallEvent, EventState
from .inspect import (
    get_child_spec,
    get_spec_class_type,
    is_async_callable,
    is_awaitable,
    is_magic_attribute,
)
from .state import AttributeRehearsal, DecoyState, MockInfo


class MockInternals:
    def __init__(
        self,
        state: DecoyState,
        spec: Any,
        name: str,
        full_name: Optional[str],
        spec_class_type: Type[Any],
    ) -> None:
        self.state = state
        self.spec = spec
        self.name = name
        self.full_name = full_name or name
        self.spec_class_type = spec_class_type
        self.attributes: Dict[str, Any] = {}
        self.deleted_attributes: Set[str] = set()
        self.event_state = EventState(is_entered=False)
        self.info = MockInfo(id(self), self.full_name)


class Mock:
    _decoy: MockInternals

    def __init__(self, internals: MockInternals) -> None:
        super().__setattr__("_decoy", internals)

    @property  # type: ignore[misc]
    def __class__(self) -> Type[Any]:
        """Ensure Spy can pass `isinstance` checks."""
        return self._decoy.spec_class_type

    def __repr__(self) -> str:
        return f"<Decoy mock '{self._decoy.full_name}'>"

    def __enter__(self) -> None:
        self._decoy.event_state = EventState(is_entered=True)

    def __exit__(self, *_: Any) -> None:
        self._decoy.event_state = EventState(is_entered=False)

    def __getattr__(self, name: str) -> Any:
        behavior = self._decoy.state.use_attribute_behavior(
            self._decoy.info,
            AttributeEvent.get(name),
            self._decoy.event_state,
        )

        if behavior:
            return _trigger_behavior(behavior)

        if is_magic_attribute(name) or name in self._decoy.deleted_attributes:
            return super().__getattribute__(name)

        return self._decoy_get_child(name)

    def __setattr__(self, name: str, value: Any) -> None:
        behavior = self._decoy.state.use_attribute_behavior(
            self._decoy.info,
            AttributeEvent.set(name, value),
            self._decoy.event_state,
        )

        if behavior:
            _trigger_behavior(behavior, (value,))
            return

        self._decoy.attributes[name] = value

    def __delattr__(self, name: str) -> None:
        behavior = self._decoy.state.use_attribute_behavior(
            self._decoy.info,
            AttributeEvent.delete(name),
            self._decoy.event_state,
        )

        if behavior:
            _trigger_behavior(behavior)
            return

        self._decoy.deleted_attributes.add(name)
        self._decoy.attributes.pop(name, None)

    def _decoy_call(self, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Any:
        behavior = self._decoy.state.use_call_behavior(
            self._decoy.info,
            CallEvent(args, kwargs),
            self._decoy.event_state,
        )

        return _trigger_behavior(behavior or Behavior(), args, kwargs)

    def _decoy_get_child(self, name: str) -> Any:
        if name in self._decoy.attributes:
            return self._decoy.attributes[name]

        spec = get_child_spec(self._decoy.spec, name)
        child = create_mock(
            spec=spec,
            name=name,
            is_async=is_async_callable(spec),
            parent_name=self._decoy.full_name,
            state=self._decoy.state,
        )

        self._decoy.attributes[name] = child

        return child


class SyncMock(Mock):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._decoy_call(args, kwargs)


class AsyncMock(Mock):
    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        result = self._decoy_call(args, kwargs)

        if not is_awaitable(result):
            return result

        return await result


def create_mock(
    spec: Any,
    name: str,
    parent_name: Optional[str],
    is_async: bool,
    state: DecoyState,
) -> Mock:
    cls = AsyncMock if is_async else SyncMock
    mock_internals = MockInternals(
        state=state,
        spec=spec,
        name=name,
        full_name=name if parent_name is None else f"{parent_name}.{name}",
        spec_class_type=get_spec_class_type(spec, cls),
    )

    return cls(mock_internals)


def ensure_mock_info(method_name: str, maybe_mock: Any) -> MockInfo:
    if not isinstance(maybe_mock, Mock):
        raise NotAMockError(
            f"`Decoy.{method_name}` must be called with a mock, but got: {maybe_mock}"
        )

    return maybe_mock._decoy.info


def ensure_attribute_rehearsal(
    method_name: str,
    maybe_rehearsal: Optional[AttributeRehearsal],
    actual: Any,
) -> AttributeRehearsal:
    if maybe_rehearsal is None:
        raise NotAMockError(
            f"`AttributeDecoy.{method_name}` must be called with a mock, but got: {actual}"
        )

    return maybe_rehearsal


def _trigger_behavior(
    behavior: Behavior,
    args: Optional[Tuple[Any, ...]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
) -> Any:
    args = args or ()
    kwargs = kwargs or {}

    if behavior.error:
        raise behavior.error

    if behavior.action:
        return behavior.action(*args, **kwargs)

    if behavior.context is not MISSING:
        return contextlib.nullcontext(behavior.context)

    return behavior.return_value
