import collections.abc
import contextlib
from typing import (
    Any,
    Callable,
    Literal,
    Never,
    overload,
)

from .event import MatchOptions
from .inspect import (
    ensure_spec,
    ensure_spec_name,
    get_spec_module_name,
    is_async_callable,
)
from .mock import AsyncMock, Mock, create_mock, ensure_mock
from .state import DecoyState
from .types import (
    ClassT,
    ContextValueT,
    FuncT,
    MockT,
    ParamsT,
    ReturnT,
    SpecT,
)
from .verify import Verify
from .when import When


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

    @classmethod
    @contextlib.contextmanager
    def create(cls) -> collections.abc.Iterator["Decoy"]:
        """Create a Decoy instance for testing that will reset after usage."""
        decoy = cls()
        yield decoy
        decoy.reset()

    def __init__(self) -> None:
        self._state = DecoyState()

    @overload
    def mock(self, *, cls: Callable[..., ClassT]) -> ClassT: ...

    @overload
    def mock(self, *, func: FuncT) -> FuncT: ...

    @overload
    def mock(self, *, name: str, is_async: Literal[True]) -> AsyncMock: ...

    @overload
    def mock(self, *, name: str, is_async: bool = False) -> Mock: ...

    def mock(
        self,
        *,
        cls: Callable[..., ClassT] | None = None,
        func: FuncT | None = None,
        name: str | None = None,
        is_async: bool = False,
    ) -> ClassT | FuncT | AsyncMock | Mock:
        """Create a mock. See the [mock creation guide][] for more details.

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

    @overload
    def when(  # type: ignore[overload-overlap]
        self,
        mock: MockT[ContextValueT, ParamsT, ReturnT],
        *,
        times: int | None = None,
        ignore_extra_args: bool = False,
        is_entered: bool | None = None,
    ) -> When[Never, ParamsT, ReturnT, ContextValueT]: ...

    @overload
    def when(
        self,
        mock: SpecT,
        *,
        times: int | None = None,
        ignore_extra_args: bool = False,
        is_entered: bool | None = None,
    ) -> When[SpecT, [], Never, Never]: ...

    def when(
        self,
        mock: Any,
        *,
        times: int | None = None,
        ignore_extra_args: bool = False,
        is_entered: bool | None = None,
    ) -> When[Any, Any, Any, Any]:
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
        mock_info = ensure_mock("when", mock)
        match_options = MatchOptions(times, ignore_extra_args, is_entered)

        return When(self._state, mock_info, match_options)

    def verify(
        self,
        mock: SpecT,
        *,
        times: int | None = None,
        ignore_extra_args: bool = False,
        is_entered: bool | None = None,
    ) -> Verify[SpecT]:
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
        mock_info = ensure_mock("verify", mock)
        match_options = MatchOptions(times, ignore_extra_args, is_entered)

        return Verify(self._state, mock_info, match_options)

    def reset(self) -> None:
        """Reset the decoy instance."""
        self._state.reset()
