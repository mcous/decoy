"""Decoy test double stubbing and verification library."""

from mock import AsyncMock, MagicMock
from typing import cast, Any, Callable, Mapping, Optional, Sequence, Tuple, Type

from .registry import Registry
from .stub import Stub
from .types import Call, ClassT, FuncT, ReturnT


class Decoy:
    """Decoy test double state container."""

    _registry: Registry
    _last_decoy_id: Optional[int]

    def __init__(self) -> None:
        """
        Initialize the state container for test doubles and stubs.

        You should initialize a new Decoy instance for every test.

        Example:
            ```python
            import pytest
            from decoy import Decoy

            @pytest.fixture
            def decoy() -> Decoy:
                return Decoy()
            ```
        """
        self._registry = Registry()
        self._last_decoy_id = None

    def create_decoy(self, spec: Type[ClassT], *, is_async: bool = False) -> ClassT:
        """
        Create a class decoy for `spec`.

        Arguments:
            spec: A class definition that the decoy should mirror.
            is_async: Set to `True` if the class has `await`able methods.

        Returns:
            A `MagicMock` or `AsyncMock`, typecast as an instance of `spec`.

        Example:
            ```python
            def test_get_something(decoy: Decoy):
                db = decoy.create_decoy(spec=Database)
                # ...
            ```

        """
        decoy = MagicMock(spec=spec) if is_async is False else AsyncMock(spec=spec)
        decoy_id = self._registry.register_decoy(decoy)
        side_effect = self._create_track_call_and_act(decoy_id)

        decoy.configure_mock(
            **{
                f"{method}.side_effect": side_effect
                for method in dir(spec)
                if not (method.startswith("__") and method.endswith("__"))
            }
        )

        return cast(ClassT, decoy)

    def create_decoy_func(
        self, spec: Optional[FuncT] = None, *, is_async: bool = False
    ) -> FuncT:
        """
        Create a function decoy for `spec`.

        Arguments:
            spec: A function that the decoy should mirror.
            is_async: Set to `True` if the function is `await`able.

        Returns:
            A `MagicMock` or `AsyncMock`, typecast as the function given for `spec`.

        Example:
            ```python
            def test_create_something(decoy: Decoy):
                gen_id = decoy.create_decoy_func(spec=generate_unique_id)
                # ...
            ```
        """
        decoy = MagicMock(spec=spec) if is_async is False else AsyncMock(spec=spec)
        decoy_id = self._registry.register_decoy(decoy)

        decoy.configure_mock(side_effect=self._create_track_call_and_act(decoy_id))

        return cast(FuncT, decoy)

    def when(self, _rehearsal_result: ReturnT) -> Stub[ReturnT]:
        """
        Create a [Stub][decoy.stub.Stub] configuration using a rehearsal call.

        See [stubbing](/#stubbing) for more details.

        Arguments:
            _rehearsal_result: The return value of a rehearsal, used for typechecking.

        Returns:
            A Stub to configure using `then_return` or `then_raise`.

        Example:
            ```python
            db = decoy.create_decoy(spec=Database)
            decoy.when(db.exists("some-id")).then_return(True)
            ```
        """
        decoy_id, rehearsal = self._pop_last_rehearsal()
        stub = Stub[ReturnT](rehearsal=rehearsal)

        self._registry.register_stub(decoy_id, stub)

        return stub

    def verify(self, _rehearsal_result: ReturnT) -> None:
        """
        Verify a decoy was called using a rehearsal.

        See [verification](/#verification) for more details.

        Arguments:
            _rehearsal_result: The return value of a rehearsal, unused.

        Example:
            ```python
            def test_create_something(decoy: Decoy):
                gen_id = decoy.create_decoy_func(spec=generate_unique_id)

                # ...

                decoy.verify(gen_id("model-prefix_"))
            ```
        """
        decoy_id, rehearsal = self._pop_last_rehearsal()
        decoy = self._registry.get_decoy(decoy_id)

        if decoy is None:
            raise ValueError("verify must be called with a decoy rehearsal")

        decoy.assert_has_calls([rehearsal])

    def _pop_last_rehearsal(self) -> Tuple[int, Call]:
        decoy_id = self._last_decoy_id

        if decoy_id is not None:
            rehearsal = self._registry.pop_decoy_last_call(decoy_id)
            self._last_decoy_id = None

            if rehearsal is not None:
                return (decoy_id, rehearsal)

        raise ValueError("when/verify must be called with a decoy rehearsal")

    def _create_track_call_and_act(self, decoy_id: int) -> Callable[..., Any]:
        def track_call_and_act(
            *args: Sequence[Any], **_kwargs: Mapping[str, Any]
        ) -> Any:
            self._last_decoy_id = decoy_id

            last_call = self._registry.peek_decoy_last_call(decoy_id)
            stubs = reversed(self._registry.get_decoy_stubs(decoy_id))

            if last_call is not None:
                for stub in stubs:
                    if stub._rehearsal == last_call:
                        return stub._act()

            return None

        return track_call_and_act
