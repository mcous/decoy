import collections.abc
import functools
import re
import sys
from typing import Any, Callable, Generic, TypeVar, cast, overload

if sys.version_info >= (3, 13):
    from typing import TypeIs
else:
    from typing_extensions import TypeIs

from .errors import createNoMatcherValueCapturedError
from .inspect import get_func_name

ValueT = TypeVar("ValueT")
MatchT = TypeVar("MatchT")
MappingT = TypeVar("MappingT", bound=collections.abc.Mapping[Any, Any])
SequenceT = TypeVar("SequenceT", bound=collections.abc.Sequence[Any])
ErrorT = TypeVar("ErrorT", bound=BaseException)

TypedMatch = Callable[[object], TypeIs[MatchT]]
UntypedMatch = Callable[[object], bool]


class Matcher(Generic[ValueT]):
    """Create an [argument matcher](./matchers.md).

    Arguments:
        match: A comparison function that returns a bool or `TypeIs` guard.
        name: Optional name for the matcher; defaults to `match.__name__`
        description: Optional extra description for the matcher's repr.

    Example:
        Use a function to create a custom matcher.

        ```python
        def is_even(target: object) -> TypeIs[int]:
            return isinstance(target, int) and target % 2 == 0

        is_even_matcher = Matcher(is_even)
        ```

        Matchers can also be constructed from built-in inspection functions, like `callable`.

        ```python
        callable_matcher = Matcher(callable)
        ```
    """

    @overload
    def __init__(
        self: "Matcher[MatchT]",
        match: TypedMatch[MatchT],
        name: str | None = None,
        description: str | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self: "Matcher[Any]",
        match: UntypedMatch,
        name: str | None = None,
        description: str | None = None,
    ) -> None: ...

    def __init__(
        self,
        match: TypedMatch[ValueT] | UntypedMatch,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        self._match = match
        self._name = name or get_func_name(match)
        self._description = description
        self._values: list[ValueT] = []

    def __eq__(self, target: object) -> bool:
        if self._match(target):
            self._values.append(cast(ValueT, target))  # type: ignore[redundant-cast]
            return True

        return False

    def __repr__(self) -> str:
        matcher_name = f"Matcher.{self._name}"
        if self._description:
            return f"<{matcher_name} {self._description.strip()}>"

        return f"<{matcher_name}>"

    @property
    def arg(self) -> ValueT:
        """Type-cast the matcher as the expected value.

        Example:
            If the mock expects a `str` argument, using `arg` prevents the type-checker from raising an error.

            ```python
            decoy
              .when(mock)
              .called_with(Matcher.matches("^(hello|hi)$").arg)
              .then_return("world")
            ```
        """
        return cast(ValueT, self)

    @property
    def value(self) -> ValueT:
        """The latest matching compared value.

        Raises:
            NoMatcherValueCapturedError: the matcher has not been compared with any matching value.

        Example:
            You can use `value` to trigger a callback passed to your mock.

            ```python
            callback_matcher = Matcher(callable)
            decoy.verify(mock).called_with(callback_matcher)
            callback_matcher.value("value")
            ```
        """
        if len(self._values) == 0:
            raise createNoMatcherValueCapturedError(
                f"{self} has not matched any values"
            )

        return self._values[-1]

    @property
    def values(self) -> list[ValueT]:
        """All matching compared values."""
        return self._values.copy()

    @overload
    @staticmethod
    def any(
        type: type[MatchT],
        attrs: collections.abc.Mapping[str, object] | None = None,
    ) -> "Matcher[MatchT]": ...

    @overload
    @staticmethod
    def any(
        type: None = None,
        attrs: collections.abc.Mapping[str, object] | None = None,
    ) -> "Matcher[Any]": ...

    @staticmethod
    def any(
        type: type[MatchT] | None = None,
        attrs: collections.abc.Mapping[str, object] | None = None,
    ) -> "Matcher[MatchT] | Matcher[Any]":
        """Match an argument, optionally by type and/or attributes.

        If type and attributes are omitted, will match everything,
        including `None`.

        Arguments:
            type: Type to match, if any.
            attrs: Set of attributes to match, if any.
        """
        description = ""

        if type:
            description = type.__name__

        if attrs:
            description = f"{description} attrs={attrs!r}"

        return Matcher(
            match=functools.partial(any, type, attrs),
            description=description,
        )

    @staticmethod
    def is_not(value: object) -> "Matcher[Any]":
        """Match any value that does not `==` the given value.

        Arguments:
            value: The value that the matcher rejects.
        """
        return Matcher(
            lambda t: t != value,
            name="is_not",
            description=repr(value),
        )

    @overload
    @staticmethod
    def contains(values: MappingT) -> "Matcher[MappingT]": ...

    @overload
    @staticmethod
    def contains(values: SequenceT, in_order: bool = False) -> "Matcher[SequenceT]": ...

    @staticmethod
    def contains(
        values: MappingT | SequenceT,
        in_order: bool = False,
    ) -> "Matcher[MappingT] | Matcher[SequenceT]":
        """Match a dict, list, or string with a partial value.

        Arguments:
            values: Partial value to match.
            in_order: Match list values in order.
        """
        description = repr(values)

        if in_order:
            description = f"{description} in_order={in_order}"

        return Matcher(
            match=functools.partial(contains, values, in_order),
            description=description,
        )

    @staticmethod
    def matches(pattern: str) -> "Matcher[str]":
        """Match a string by a pattern.

        Arguments:
            pattern: Regular expression pattern.
        """
        pattern_re = re.compile(pattern)

        return Matcher(
            match=functools.partial(matches, pattern_re),
            description=repr(pattern),
        )

    @staticmethod
    def error(type: type[ErrorT], message: str | None = None) -> "Matcher[ErrorT]":
        """Match an exception object.

        Arguments:
            type: The type of exception to match.
            message: An optional regular expression pattern to match.
        """
        message_re = re.compile(message or "")
        description = type.__name__

        if message:
            description = f"{description} message={message!r}"

        return Matcher(
            match=functools.partial(error, type, message_re),
            name="error",
            description=description,
        )


def any(
    match_type: type[Any] | None,
    attrs: collections.abc.Mapping[str, object] | None,
    target: object,
) -> bool:
    return (match_type is None or isinstance(target, match_type)) and (
        attrs is None or _has_attrs(attrs, target)
    )


def _has_attrs(
    attributes: collections.abc.Mapping[str, object],
    target: object,
) -> bool:
    return all(
        hasattr(target, attr_name) and getattr(target, attr_name) == attr_value
        for attr_name, attr_value in attributes.items()
    )


def contains(
    values: collections.abc.Mapping[object, object] | collections.abc.Sequence[object],
    in_order: bool,
    target: object,
) -> bool:
    if isinstance(values, collections.abc.Mapping):
        return _dict_containing(values, target)
    if isinstance(values, str):
        return isinstance(target, str) and values in target

    return _list_containing(values, in_order, target)


def _dict_containing(
    values: collections.abc.Mapping[object, object],
    target: object,
) -> bool:
    try:
        return all(
            attr_name in target and target[attr_name] == attr_value  # type: ignore[index,operator]
            for attr_name, attr_value in values.items()
        )
    except TypeError:
        return False


def _list_containing(
    values: collections.abc.Sequence[object],
    in_order: bool,
    target: object,
) -> bool:
    target_index = 0

    try:
        for value in values:
            if in_order:
                target = target[target_index:]  # type: ignore[index]

            target_index = target.index(value)  # type: ignore[attr-defined]

    except (AttributeError, TypeError, ValueError):
        return False

    return True


def error(
    type: type[ErrorT],
    message_pattern: re.Pattern[str],
    target: object,
) -> bool:
    return isinstance(target, type) and message_pattern.search(str(target)) is not None


def matches(pattern: re.Pattern[str], target: object) -> bool:
    return isinstance(target, str) and pattern.search(target) is not None
