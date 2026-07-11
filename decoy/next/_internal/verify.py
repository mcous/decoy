import collections.abc
import contextlib
import functools
import sys
from typing import Any, Callable, Generic, ParamSpec, TypeVar

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from ...errors import NotAMockError, VerifyError, VerifyOrderError
from ...warnings import RedundantVerifyWarning
from .inspect import bind_args
from .mock import ensure_mock
from .state import DecoyState
from .stringify import (
    stringify_redundant_verify,
    stringify_verify_failure,
    stringify_verify_order_failure,
)
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


def _ensure_mock(mock: object) -> MockInfo:
    mock_info = ensure_mock(mock)

    if not mock_info:
        raise NotAMockError(f"`verify` must be called with a mock, but got: {mock}")

    return mock_info


class _Verifier:
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
    ) -> Self:
        """Configure the verification.

        Arguments:
            times: How many times the interaction is expected.
            ignore_extra_args: Only partially match arguments.
            is_entered: Verify the interaction happens while entered using `with`.
        """
        return type(self)(
            self._state,
            MatchOptions(times, ignore_extra_args, is_entered),
        )

    def _verify_call(self, mock: MockInfo, *args: object,
    **kwargs: Dict[str, object]) -> None:

    def _verify_event(self, mock: MockInfo, expected: Event) -> None:
        matcher = EventMatcher(expected, self._match_options)
        result = self._state.use_verification(mock, matcher)

        if not result.is_success:
            if result.order_anchor is not None:
                raise VerifyOrderError(
                    stringify_verify_order_failure(
                        mock.name,
                        expected,
                        result.order_anchor,
                        list(result.order_timeline),
                    )
                )

            message = stringify_verify_failure(
                mock.name,
                self._match_options,
                expected,
                result.mock_events,
            )
            raise VerifyError(message)

        if result.is_redundant:
            message = stringify_redundant_verify(mock.name, expected)
            warn(RedundantVerifyWarning(message))


class Verify(_Verifier):
    def __init__(
        self,
        state: DecoyState,
        match_options: MatchOptions | None = None,
    ) -> None:
        self._state = state
        self._match_options = match_options or MatchOptions()

    @property
    @contextlib.contextmanager
    def ordered(self) -> collections.abc.Generator["VerifyWithAttributes", None, None]:
        """Verify a sequence of interactions happened in order.

        Enter a `with` block; each verification inside must match a later
        interaction than the previous one.

        Raises:
            VerifyOrderError: An interaction happened out of the expected order.
        """
        with self._state.pause():
            with self._state.verify_order():
                yield VerifyWithAttributes(self._state, self._match_options)

    def __enter__(self) -> "VerifyWithAttributes":
        self._exit_stack = contextlib.ExitStack()
        self._exit_stack.enter_context(self._state.pause())

        return VerifyWithAttributes(self._state, self._match_options)

    def __exit__(self, *exc_info: object) -> None:
        self._exit_stack.close()
        return None

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
        mock_info = _ensure_mock(mock)
        bound_args = bind_args(
            signature=mock_info.signature,
            args=args,
            kwargs=kwargs,
            ignore_extra_args=self._match_options.ignore_extra_args,
        )
        expected = CallEvent(args=bound_args.args, kwargs=bound_args.kwargs)

        self._verify(mock_info, expected)


class VerifyWithAttributes(_Verifier):
    """Verify [attribute interactions](./attributes.md#verify-property-access).

    Entering `with decoy.verify` yields a `VerifyWithAttributes`, which adds
    [`set`][decoy.next.VerifyWithAttributes.set] and
    [`delete`][decoy.next.VerifyWithAttributes.delete] to the call verification
    available on [`Verify`][decoy.next.Verify].
    """

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
        mock_info = _ensure_mock(mock)
        bound_args = bind_args(
            signature=mock_info.signature,
            args=args,
            kwargs=kwargs,
            ignore_extra_args=self._match_options.ignore_extra_args,
        )
        expected = CallEvent(args=bound_args.args, kwargs=bound_args.kwargs)

        self._verify(mock_info, expected)

    def set(self, attribute: SpecT) -> "VerifySet[SpecT]":
        """Verify that an [attribute was set](./attributes.md#verify-a-setter).

        Pass the set value to [`VerifySet.to`][decoy.next.VerifySet.to].

        Raises:
            NotAMockError: `attribute` is invalid.
        """
        mock_info = _ensure_mock(attribute)
        return VerifySet(functools.partial(self._verify, mock_info))

    def delete(self, attribute: object) -> None:
        """Verify that an [attribute was deleted](./attributes.md#verify-a-deleter).

        Raises:
            NotAMockError: `attribute` is invalid.
        """
        mock_info = _ensure_mock(attribute)
        expected = AttributeEvent.delete()

        self._verify(mock_info, expected)


class VerifySet(Generic[SpecT]):
    """Verify that an [attribute was set](./attributes.md#verify-a-setter).

    Created by [`VerifyWithAttributes.set`][decoy.next.VerifyWithAttributes.set];
    pass the value to `to`.
    """

    def __init__(self, verify: Callable[[Event], None]) -> None:
        self._verify = verify

    def to(self, value: SpecT) -> None:
        """Verify the attribute was set to `value`."""
        self._verify(AttributeEvent.set(value))
