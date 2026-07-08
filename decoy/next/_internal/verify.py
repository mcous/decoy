from typing import Any, Callable, Generic, ParamSpec, TypeVar

from ...errors import NotAMockError, VerifyError
from ...warnings import RedundantVerifyWarning
from .inspect import bind_args
from .mock import ensure_mock
from .state import DecoyState
from .stringify import stringify_redundant_verify, stringify_verify_failure
from .values import (
    AttributeEvent,
    CallEvent,
    Event,
    EventMatcher,
    MatchOptions,
    MockInfo,
)
from .warn import warn

SpecT = TypeVar("SpecT")
ParamsT = ParamSpec("ParamsT")


def _run_verification(
    state: DecoyState,
    match_options: MatchOptions,
    mock: MockInfo,
    expected: Event,
) -> None:
    matcher = EventMatcher(expected, match_options)
    result = state.use_verification(mock, matcher)

    if not result.is_success:
        message = stringify_verify_failure(
            mock.name,
            match_options,
            expected,
            result.mock_events,
        )
        raise VerifyError(message)

    if result.is_redundant:
        message = stringify_redundant_verify(mock.name, expected)
        warn(RedundantVerifyWarning(message))


class VerifySet(Generic[SpecT]):
    """Verify that an [attribute was set](./attributes.md#verify-a-setter).

    Created by [`Verify.set`][decoy.next.Verify.set]; pass the value to `to`.
    """

    def __init__(
        self,
        state: DecoyState,
        mock: MockInfo,
        match_options: MatchOptions,
    ) -> None:
        self._state = state
        self._mock = mock
        self._match_options = match_options

    def to(self, value: SpecT) -> None:
        """Verify the attribute was set to `value`."""
        _run_verification(
            self._state,
            self._match_options,
            self._mock,
            AttributeEvent.set(value),
        )


class Verify:
    """[Verify](./verify.md) how a mock was triggered."""

    def __init__(
        self,
        state: DecoyState,
        match_options: MatchOptions | None = None,
    ) -> None:
        self._state = state
        self._match_options = match_options or MatchOptions()

    def __call__(
        self,
        *,
        times: int | None = None,
        ignore_extra_args: bool = False,
        is_entered: bool | None = None,
    ) -> "Verify":
        """Configure the verification.

        Arguments:
            times: How many times the interaction is expected.
            ignore_extra_args: Only partially match arguments.
            is_entered: Verify the interaction happens while entered using `with`.
        """
        return Verify(
            self._state,
            MatchOptions(times, ignore_extra_args, is_entered),
        )

    def called(
        self,
        mock: Callable[ParamsT, Any],
        *args: ParamsT.args,
        **kwargs: ParamsT.kwargs,
    ) -> None:
        """Verify that a mock was called.

        Raises:
            NotAMockError: `mock` is invalid.
        """
        mock_info = self._ensure_mock(mock)
        bound_args = bind_args(
            signature=mock_info.signature,
            args=args,
            kwargs=kwargs,
            ignore_extra_args=self._match_options.ignore_extra_args,
        )
        expected = CallEvent(args=bound_args.args, kwargs=bound_args.kwargs)

        self._verify(mock_info, expected)

    def set(self, attribute: SpecT) -> VerifySet[SpecT]:
        """Verify that an [attribute was set](./attributes.md#verify-a-setter).

        Pass the set value to [`VerifySet.to`][decoy.next.VerifySet.to].

        Raises:
            NotAMockError: `attribute` is invalid.
        """
        mock_info = self._ensure_mock(attribute)
        return VerifySet(self._state, mock_info, self._match_options)

    def delete(self, attribute: object) -> None:
        """Verify that an [attribute was deleted](./attributes.md#verify-a-deleter).

        Raises:
            NotAMockError: `mock` is invalid.
        """
        mock_info = self._ensure_mock(attribute)
        expected = AttributeEvent.delete()

        self._verify(mock_info, expected)

    def _ensure_mock(self, mock: object) -> MockInfo:
        mock_info = ensure_mock(mock)

        if not mock_info:
            mock_info = self._state.peek_last_attribute_mock(mock)

        if not mock_info:
            raise NotAMockError(
                f"`Decoy.verify` must be called with a mock, but got: {mock}"
            )

        return mock_info

    def _verify(self, mock: MockInfo, expected: Event) -> None:
        _run_verification(self._state, self._match_options, mock, expected)
