import collections.abc
import re
from typing import Any, Callable, Generic, TypeVar, cast, overload

try:
    from typing import TypeIs
except ImportError:
    from typing_extensions import TypeIs

from .errors import createNoMatcherValueCapturedError

ValueT = TypeVar("ValueT")
MatchT = TypeVar("MatchT")
DictT = TypeVar("DictT", bound=collections.abc.Mapping[Any, Any])
ListT = TypeVar("ListT", bound=collections.abc.Sequence[Any])
ErrorT = TypeVar("ErrorT", bound=BaseException)

TypedMatch = Callable[[object], TypeIs[MatchT]]
UntypedMatch = Callable[[object], bool]


class Matcher(Generic[ValueT]):
    """Create a matcher from a comparison function.

    Arguments:
        match: A comparison function that returns bool or `TypeIs` guard.
        name: Optional name for the matcher's repr; defaults to `match.__name__`
        description: Optional extra description for the matcher's repr.

    Example:
        Matchers can be constructed from built-in inspection functions, like `callable`.

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
        self._name = name or match.__name__
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
              .called_with(Matcher.string("^hello").arg)
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

    @staticmethod
    def any() -> "Matcher[Any]":
        """Match everything, including `None`."""
        return Matcher(lambda _: True, name="any")

    @staticmethod
    def something() -> "Matcher[Any]":
        """Match everything except `None`."""
        return Matcher(lambda t: t is not None, name="something")

    @staticmethod
    def is_a(
        match_type: type[MatchT],
        attributes: collections.abc.Mapping[str, object] | None = None,
    ) -> "Matcher[MatchT]":
        """Match if `isinstance` matches the given type.

        Can optionally also match a set of attributes on the target object.

        Arguments:
            match_type: Type to match.
            attributes: Optional set of attributes to match.
        """
        description = match_type.__name__

        if attributes is not None:
            description = f"{description} {attributes!r}"

        return Matcher(
            lambda t: isinstance(t, match_type) and _has_attrs(t, attributes),
            name="is_a",
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

    @staticmethod
    def has_attrs(attributes: collections.abc.Mapping[str, object]) -> "Matcher[Any]":
        """Match a partial set of attributes on the target object.

        Arguments:
            attributes: Partial set of attributes to match.
        """
        return Matcher(
            lambda t: _has_attrs(t, attributes),
            name="has_attrs",
            description=repr(attributes),
        )

    @staticmethod
    def dict_containing(values: DictT) -> "Matcher[DictT]":
        """Match a mapping containing at least the given values.

        Arguments:
            values: Partial mapping to match.
        """
        return Matcher(
            lambda t: _dict_containing(t, values),
            name="dict_containing",
            description=repr(values),
        )

    @staticmethod
    def list_containing(values: ListT, in_order: bool = False) -> "Matcher[ListT]":
        """Match a sequence containing at least the given values.

        Arguments:
            values: Partial sequence to match.
            in_order: Match sequence order
        """
        description = repr(values)

        if in_order:
            description = f"{description} {in_order=}"

        return Matcher(
            lambda t: _list_containing(t, values, in_order),
            name="list_containing",
            description=description,
        )

    @staticmethod
    def string(pattern: str) -> "Matcher[str]":
        """Match a string by a pattern.

        Arguments:
            pattern: Regular expression pattern.
        """
        pattern_re = re.compile(pattern)

        return Matcher(
            lambda t: isinstance(t, str) and pattern_re.search(t) is not None,
            name="string",
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
            description = f"{description} {message!r}"

        return Matcher(
            lambda t: isinstance(t, type) and message_re.search(str(t)) is not None,
            name="error",
            description=description,
        )


def _has_attrs(
    target: object,
    attributes: collections.abc.Mapping[str, object] | None,
) -> bool:
    attributes = attributes or {}

    return all(
        hasattr(target, attr_name) and getattr(target, attr_name) == attr_value
        for attr_name, attr_value in attributes.items()
    )


def _dict_containing(
    target: object,
    values: collections.abc.Mapping[object, object],
) -> bool:
    try:
        return all(
            attr_name in target and target[attr_name] == attr_value  # type: ignore[index,operator]
            for attr_name, attr_value in values.items()
        )
    except TypeError:
        return False


def _list_containing(
    target: object,
    values: collections.abc.Sequence[object],
    in_order: bool,
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
