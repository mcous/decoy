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


class Verifier:
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


class Verify(Verifier, Generic[SpecT]):
    def called_with(
        self: "Verify[Callable[ParamsT, Any]]",
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> None:
        bound_args = bind_args(self._mock.signature, args, kwargs)
        expected = CallEvent(args=bound_args.args, kwargs=bound_args.kwargs)

        self._verify(expected)


class AttributesVerify(Verifier, Generic[SpecT]):
    def set_with(self, value: SpecT) -> None:
        expected = AttributeEvent.set(value)

        self._verify(expected)

    def delete(self) -> None:
        expected = AttributeEvent.delete()

        self._verify(expected)
