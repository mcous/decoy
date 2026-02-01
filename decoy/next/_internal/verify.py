import warnings
from typing import Any, Callable, Generic, ParamSpec, TypeVar

from .errors import createVerifyError
from .inspect import bind_args
from .state import DecoyState
from .values import (
    AttributeEvent,
    CallEvent,
    Event,
    EventMatcher,
    MatchOptions,
    MockInfo,
)
from .warnings import createRedundantVerifyWarning

SpecT = TypeVar("SpecT")
ParamsT = ParamSpec("ParamsT")


class Verify(Generic[SpecT]):
    """[Verify](./verify.md) how a mock was called."""

    def __init__(
        self,
        state: DecoyState,
        mock: MockInfo,
        match_options: MatchOptions,
    ) -> None:
        self._mock = mock
        self._state = state
        self._match_options = match_options

    def _verify(self, expected: Event) -> None:
        matcher = EventMatcher(expected, self._match_options)
        result = self._state.use_verification(self._mock, matcher)

        if not result.is_success:
            raise createVerifyError(
                self._mock.name,
                self._match_options,
                expected,
                result.mock_events,
            )

        if result.is_redundant:
            warnings.warn(
                createRedundantVerifyWarning(self._mock.name, expected),
                stacklevel=3,
            )

    def called_with(
        self: "Verify[Callable[ParamsT, Any]]",
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> None:
        """Verify that a mock was called."""
        bound_args = bind_args(
            signature=self._mock.signature,
            args=args,
            kwargs=kwargs,
            ignore_extra_args=self._match_options.ignore_extra_args,
        )
        expected = CallEvent(args=bound_args.args, kwargs=bound_args.kwargs)

        self._verify(expected)

    def set(self, value: SpecT) -> None:
        """Verify that an [attribute was set](./attributes.md#verify-a-setter)."""
        expected = AttributeEvent.set(value)

        self._verify(expected)

    def delete(self) -> None:
        """Verify that an [attribute was deleted](./attributes.md#verify-a-deleter)."""
        expected = AttributeEvent.delete()

        self._verify(expected)
