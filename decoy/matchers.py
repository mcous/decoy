"""Matcher helpers.

A "matcher" is a class with an `__eq__` method defined. Use them anywhere
in your test where you would use an actual value for equality (`==`) comparison.

Matchers help you loosen assertions where strict adherence to an exact value
is not relevant to what you're trying to test.
See the [matchers guide][] for more details.

[matchers guide]: usage/matchers.md

!!! example
    ```python
    from decoy import Decoy, matchers

    # ...

    def test_logger_called(decoy: Decoy):
        # ...
        decoy.verify(
            logger.log(msg=matchers.StringMatching("hello"))
        )
    ```

!!! note
    Identity comparisons (`is`) will not work with matchers. Decoy only uses
    equality comparisons (`==`) for stubbing and verification.
"""

from abc import ABC, abstractmethod
from re import compile as compile_re, Pattern
from typing import cast, TypeVar, Generic, Any, override, overload
from collections.abc import Iterable, Mapping
from warnings import deprecated


__all__ = [
    "Anything",
    "AnythingOrNone",
    "ArgumentCaptor",
    "Captor",
    "ErrorMatching",
    "IsA",
    "IsNot",
    "StringMatching",
    "argument_captor",
]


MatchT = TypeVar("MatchT", default=Any)


class _AnythingOrNone:
    def __eq__(self, target: object) -> bool:
        return True

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return "<AnythingOrNone>"


def AnythingOrNone() -> MatchT:  # type: ignore[type-var]
    """Match anything including None.

    !!! example
        ```python
        assert "foobar" == AnythingOrNone()
        assert None == AnythingOrNone()
        ```
    """
    return cast(MatchT, _AnythingOrNone())


class _Anything:
    def __eq__(self, target: object) -> bool:
        """Return true if target is not None."""
        return target is not None

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return "<Anything>"


def Anything() -> MatchT:  # type: ignore[type-var]
    """Match anything except None.

    !!! example
        ```python
        assert "foobar" == Anything()
        assert None != Anything()
        ```
    """
    return cast(MatchT, _Anything())


class _IsA:
    _match_type: type[object]
    _attributes: Mapping[str, object] | None

    def __init__(
        self,
        match_type: type[object],
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        """Initialize the matcher with a type and optional attributes."""
        self._match_type = match_type
        self._attributes = attributes

    def __eq__(self, target: object) -> bool:
        """Return true if target is the correct type and matches attributes."""
        matches_type = isinstance(target, self._match_type)
        matches_attrs = (
            target == HasAttributes(self._attributes) if self._attributes else True
        )

        return matches_type and matches_attrs

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        if self._attributes is None:
            return f"<IsA {self._match_type.__name__}>"
        else:
            return f"<IsA {self._match_type.__name__} {self._attributes!r}>"


def IsA(
    match_type: type[MatchT], attributes: Mapping[str, object] | None = None
) -> MatchT:
    """Match anything that satisfies the passed in type.

    Arguments:
        match_type: Type to match.
        attributes: Optional set of attributes to match

    !!! example
        ```python
        assert "foobar" == IsA(str)
        assert datetime.now() == IsA(datetime)
        assert 42 == IsA(int)

        @dataclass
        class HelloWorld:
            hello: str = "world"
            goodby: str = "so long"

        assert HelloWorld() == IsA(HelloWorld, {"hello": "world"})
        ```
    """
    return cast(MatchT, _IsA(match_type, attributes))


class _IsNot:
    _reject_value: object

    def __init__(self, value: object) -> None:
        """Initialize the matcher with the value to reject."""
        self._reject_value = value

    def __eq__(self, target: object) -> bool:
        """Return true if target is not self._reject_value."""
        return target != self._reject_value

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return f"<IsNot {self._reject_value!r}>"


def IsNot(value: MatchT) -> MatchT:
    """Match anything that isn't the passed in value.

    Arguments:
        value: Value to check against.

    !!! example
        ```python
        assert "foobar" == IsNot("bazquux")
        assert 42 == IsNot("the question")
        assert 1 != IsNot(1)
        ```
    """
    return cast(MatchT, _IsNot(value))


class _HasAttributes:
    _attributes: Mapping[str, object]

    def __init__(self, attributes: Mapping[str, object]) -> None:
        self._attributes = attributes

    def __eq__(self, target: object) -> bool:
        """Return true if target matches all given attributes."""
        is_match = True
        for attr_name, value in self._attributes.items():
            if is_match:
                is_match = (
                    hasattr(target, attr_name) and getattr(target, attr_name) == value
                )

        return is_match

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return f"<HasAttributes {self._attributes!r}>"


def HasAttributes(attributes: Mapping[str, object]) -> MatchT:  # type: ignore[type-var]
    """Match anything with the passed in attributes.

    Arguments:
        attributes: Attribute values to check.

    !!! example
        ```python
        @dataclass
        class HelloWorld:
            hello: str = "world"
            goodby: str = "so long"

        assert HelloWorld() == matchers.HasAttributes({"hello": "world"})
        ```
    """
    return cast(MatchT, _HasAttributes(attributes))


class _DictMatching:
    _values: Mapping[str, object]

    def __init__(self, values: Mapping[str, object]) -> None:
        self._values = values

    def __eq__(self, target: object) -> bool:
        """Return true if target matches all given keys/values."""
        if not isinstance(target, Mapping):
            return False
        is_match = True

        for key, value in self._values.items():
            if is_match:
                try:
                    is_match = key in target and target[key] == value
                except TypeError:
                    is_match = False

        return is_match

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return f"<DictMatching {self._values!r}>"


def DictMatching(values: Mapping[str, MatchT]) -> Mapping[str, MatchT]:
    """Match any dictionary with the passed in keys / values.

    Arguments:
        values: Keys and values to check.

    !!! example
        ```python
        value = {"hello": "world", "goodbye": "so long"}
        assert value == matchers.DictMatching({"hello": "world"})
        ```
    """
    return cast(Mapping[str, MatchT], _DictMatching(values))


class _ListMatching:
    _values: Iterable[object]

    def __init__(self, values: Iterable[object]) -> None:
        self._values = values

    def __eq__(self, target: object) -> bool:
        """Return true if target matches all given values."""
        if not isinstance(target, Iterable):
            return False

        return all(
            any(item == target_item for target_item in target) for item in self._values
        )

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return f"<ListMatching {self._values!r}>"


def ListMatching(values: list[MatchT]) -> list[MatchT]:
    """Match any list with the passed in values.

    Arguments:
        values: Values to check.

    !!! example
        ```python
        value = [1, 2, 3]
        assert value == matchers.ListMatching([1, 2])
        ```
    """
    return cast(list[MatchT], _ListMatching(values))


class _StringMatching:
    _pattern: Pattern[str]

    def __init__(self, match: str) -> None:
        """Initialize the matcher with the pattern to match."""
        self._pattern = compile_re(match)

    def __eq__(self, target: object) -> bool:
        """Return true if target is not self._reject_value."""
        return isinstance(target, str) and self._pattern.search(target) is not None

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return f"<StringMatching {self._pattern.pattern!r}>"


def StringMatching(match: str) -> str:
    """Match any string matching the passed in pattern.

    Arguments:
        match: Pattern to check against; will be compiled into an re.Pattern.

    !!! example
        ```python
        assert "foobar" == StringMatching("bar")
        assert "foobar" != StringMatching("^bar")
        ```
    """
    return cast(str, _StringMatching(match))


class _ErrorMatching:
    _error_type: type[BaseException]
    _string_matcher: _StringMatching | None

    def __init__(self, error: type[BaseException], match: str | None = None) -> None:
        """Initialize with the Exception type and optional message matcher."""
        self._error_type = error
        self._string_matcher = _StringMatching(match) if match is not None else None

    def __eq__(self, target: object) -> bool:
        """Return true if target is not self._reject_value."""
        error_match = type(target) is self._error_type
        message_match = (
            str(target) == self._string_matcher
            if self._string_matcher is not None
            else True
        )

        return error_match and message_match

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return (
            f"<ErrorMatching {self._error_type.__name__} match={self._string_matcher}>"
        )


ErrorT = TypeVar("ErrorT", bound=BaseException)


def ErrorMatching(error: type[ErrorT], match: str | None = None) -> ErrorT:
    """Match any error matching an Exception type and optional message matcher.

    Arguments:
        error: Exception type to match against.
        match: Pattern to check against; will be compiled into an re.Pattern.

    !!! example
        ```python
        assert ValueError("oh no!") == ErrorMatching(ValueError)
        assert ValueError("oh no!") == ErrorMatching(ValueError, match="no")
        ```
    """
    return cast(ErrorT, _ErrorMatching(error, match))


CapturedT = TypeVar("CapturedT", covariant=True)


class ArgumentCaptor(ABC, Generic[CapturedT]):
    """Captures method arguments for later assertions.

    Use the `capture()` method to pass the captor as an argument when stubbing a method.
    The last captured argument is available via `captor.value`, and all captured arguments
    are stored in `captor.values`.

    !!! example
        ```python
        captor: ArgumentCaptor[str] = argument_captor(match_type=str)
        assert "foobar" == captor.capture()
        assert 2 != captor.capture()
        print(captor.value)  # "foobar"
        print(captor.values)  # ["foobar"]
        ```
    """

    @abstractmethod
    def capture(self) -> CapturedT:
        """Match anything, capturing its value.

        !!! note
            This method exists solely to match the target argument type and suppress type checker warnings.
        """

    @property
    @abstractmethod
    def value(self) -> CapturedT:
        """Get the captured value.

        Raises:
            AssertionError: if no value was captured.
        """

    @property
    @abstractmethod
    def values(self) -> list[CapturedT]:
        """Get all captured values."""


class _Captor(ArgumentCaptor[CapturedT]):
    _values: list[CapturedT]
    _match_type: type[CapturedT]

    def __init__(self, match_type: type[CapturedT]) -> None:
        self._values = []
        self._match_type = match_type

    @override
    def __eq__(self, target: object) -> bool:
        if isinstance(target, self._match_type):
            self._values.append(target)
            return True
        return False

    @override
    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return "<Captor>"

    @override
    def capture(self) -> CapturedT:
        return cast(CapturedT, self)

    @property
    @override
    def value(self) -> CapturedT:
        if len(self._values) == 0:
            raise AssertionError("No value captured by captor.")
        return self._values[-1]

    @property
    def values(self) -> list[CapturedT]:
        return self._values


@overload
def Captor() -> Any: ...
@overload
def Captor(match_type: type[MatchT]) -> MatchT: ...
@deprecated(
    "Use ArgumentCaptor() instead, and then call capture() to pass the matcher as an argument."
)
def Captor(match_type: type[object] = object) -> object:
    """Match anything, capturing its value for further assertions.

    !!! warning Deprecated
        This matcher is deprecated. Use [decoy.matchers.ArgumentCaptor][] instead.

    The last captured value will be set to `captor.value`. All captured
    values will be placed in the `captor.values` list, which can be
    helpful if a captor needs to be triggered multiple times.

    Arguments:
        match_type: Optional type to match.

    !!! example
        ```python
        captor = Captor()
        assert "foobar" == captor
        print(captor.value)  # "foobar"
        print(captor.values)  # ["foobar"]
        ```
    """
    return _Captor(match_type)


@overload
def argument_captor() -> ArgumentCaptor[Any]: ...
@overload
def argument_captor(match_type: type[MatchT]) -> ArgumentCaptor[MatchT]: ...
def argument_captor(match_type: type[object] = object) -> ArgumentCaptor[object]:
    """Create an [decoy.matchers.ArgumentCaptor][] to capture arguments of the given type.

    Arguments:
        match_type: Optional type to match.

    !!! example
        ```python
        fake = decoy.mock(cls=Dependency)
        captor = matchers.argument_captor()

        decoy.when(fake.do_thing(captor.capture())).then_return(42)

        assert captor.value == "Expected value"
        ```
    """
    return _Captor(match_type)
