import contextlib
from typing import Any, Callable, Generator, Optional, overload

from .event import MatchOptions
from .inspect import (
    ensure_spec,
    ensure_spec_name,
    get_spec_module_name,
    is_async_callable,
)
from .mock import create_mock, ensure_attribute_rehearsal, ensure_mock_info
from .state import DecoyState
from .types import ClassT, FuncT, ParamsT, ReturnT
from .verify import AttributeVerify, Verify
from .when import AttributeWhen, When


class AttributeDecoy:
    def __init__(self, state: DecoyState) -> None:
        self._state = state

    def when(self, attribute_value: ReturnT) -> AttributeWhen[ReturnT]:
        rehearsal = self._state.use_attribute_rehearsal()
        mock_id, attribute = ensure_attribute_rehearsal(
            "when", rehearsal, attribute_value
        )

        return AttributeWhen(mock_id, attribute, self._state)

    def verify(self, attribute_value: ReturnT) -> AttributeVerify[ReturnT]:
        rehearsal = self._state.use_attribute_rehearsal()
        mock_id, attribute = ensure_attribute_rehearsal(
            "verify", rehearsal, attribute_value
        )

        return AttributeVerify(mock_id, attribute, self._state)


class Decoy:
    """Decoy mock factory and state container.

    You should create a new Decoy instance before each test and call
    [`reset`][decoy.Decoy.reset] after each test. If you use the
    [`decoy` pytest fixture][decoy.pytest_plugin.decoy], this is done
    automatically. See the [setup guide][] for more details.

    !!! example
        ```python
        decoy = Decoy()

        # test your subject
        ...

        decoy.reset()
        ```

    [setup guide]: index.md#setup
    """

    def __init__(self) -> None:
        self._state = DecoyState()

    @overload
    def mock(self, *, cls: Callable[..., ClassT]) -> ClassT: ...

    @overload
    def mock(self, *, func: FuncT) -> FuncT: ...

    @overload
    def mock(self, *, name: str, is_async: bool = False) -> Any: ...

    def mock(
        self,
        *,
        cls: Optional[Callable[..., ClassT]] = None,
        func: Optional[FuncT] = None,
        name: Optional[str] = None,
        is_async: bool = False,
    ) -> Any:
        """Create a mock. See the [mock creation guide] for more details.

        [mock creation guide]: usage/create.md

        Arguments:
            cls: A class definition that the mock should imitate.
            func: A function definition the mock should imitate.
            name: A name to use for the mock. If you do not use
                `cls` or `func`, you should add a `name`.
            is_async: Force the returned spy to be asynchronous. This argument
                only applies if you don't use `cls` nor `func`.

        Returns:
            A mock typecast as the object it's imitating, if any.

        !!! example
            ```python
            def test_get_something(decoy: Decoy):
                db = decoy.mock(cls=Database)
                # ...
            ```
        """
        spec = ensure_spec(cls, func)
        name = ensure_spec_name(spec, name)
        parent_name = get_spec_module_name(spec)
        is_async = is_async_callable(spec, is_async)

        return create_mock(
            spec=spec,
            name=name,
            parent_name=parent_name,
            is_async=is_async,
            state=self._state,
        )

    def when(
        self,
        mock: Callable[ParamsT, ReturnT],
        *,
        times: Optional[int] = None,
        ignore_extra_args: bool = False,
        is_entered: bool = False,
    ) -> When[ParamsT, ReturnT]:
        """Configure a mock as a stub.

        See [stubbing usage guide](usage/when.md) for more details.

        Arguments:
            mock: The mock to configure.
            times: Limit the number of times the behavior is triggered.
            ignore_extra_args: Only partially match arguments.
            is_entered: Limit the behavior to when the mock is entered using `with`.

        Returns:
            A stub interface to configure matching arguments.

        !!! example
            ```python
            db = decoy.mock(cls=Database)
            decoy.when(db.exists).called_with("some-id").then_return(True)
            ```
        """
        mock_info = ensure_mock_info("verify", mock)
        match_options = MatchOptions(times, ignore_extra_args, is_entered)

        return When(mock_info, self._state, match_options)

    def verify(
        self,
        mock: Callable[ParamsT, Any],
        *,
        times: Optional[int] = None,
        ignore_extra_args: bool = False,
        is_entered: bool = False,
    ) -> Verify[ParamsT]:
        """Verify a mock was called using one or more rehearsals.

        See [verification usage guide](usage/verify.md) for more details.

        Arguments:
            mock: The mock to verify.
            times: Limit the number of times the call is expected.
            ignore_extra_args: Only partially match arguments.
            is_entered: Verify call happens when the mock is entered using `with`.

        Raises:
            VerifyError: The verification was not satisfied.

        !!! example
            ```python
            def test_create_something(decoy: Decoy):
                gen_id = decoy.mock(func=generate_unique_id)

                # ...

                decoy.verify(gen_id).called_with("model-prefix_")
            ```
        """
        mock_info = ensure_mock_info("verify", mock)
        match_options = MatchOptions(times, ignore_extra_args, is_entered)

        return Verify(mock_info, self._state, match_options)

    @contextlib.contextmanager
    def attribute(self) -> Generator[AttributeDecoy, None, None]:
        with self._state.rehearse_attributes():
            yield AttributeDecoy(self._state)

    def reset(self) -> None:
        self._state.reset()
