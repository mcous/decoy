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

from re import compile as compile_re
from typing import cast, Any, List, Mapping, Optional, Pattern, Type, TypeVar


__all__ = [
    "Anything",
    "Captor",
    "ErrorMatching",
    "IsA",
    "IsNot",
    "StringMatching",
]


class _AnythingOrNone:
    def __eq__(self, target: object) -> bool:
        return True

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return "<AnythingOrNone>"


def AnythingOrNone() -> Any:
    """Match anything including None.

    !!! example
        ```python
        assert "foobar" == AnythingOrNone()
        assert None == AnythingOrNone()
        ```
    """
    return _AnythingOrNone()


class _Anything:
    def __eq__(self, target: object) -> bool:
        """Return true if target is not None."""
        return target is not None

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return "<Anything>"


def Anything() -> Any:
    """Match anything except None.

    !!! example
        ```python
        assert "foobar" == Anything()
        assert None != Anything()
        ```
    """
    return _Anything()


class _IsA:
    _match_type: type
    _attributes: Optional[Mapping[str, Any]]

    def __init__(
        self,
        match_type: type,
        attributes: Optional[Mapping[str, Any]] = None,
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


def IsA(match_type: type, attributes: Optional[Mapping[str, Any]] = None) -> Any:
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
    return _IsA(match_type, attributes)


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


def IsNot(value: object) -> Any:
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
    return _IsNot(value)


class _HasAttributes:
    _attributes: Mapping[str, Any]

    def __init__(self, attributes: Mapping[str, Any]) -> None:
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


def HasAttributes(attributes: Mapping[str, Any]) -> Any:
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
    return _HasAttributes(attributes)


class _DictMatching:
    _values: Mapping[str, Any]

    def __init__(self, values: Mapping[str, Any]) -> None:
        self._values = values

    def __eq__(self, target: object) -> bool:
        """Return true if target matches all given keys/values."""
        is_match = True

        for key, value in self._values.items():
            if is_match:
                try:
                    is_match = key in target and target[key] == value  # type: ignore[index,operator]
                except TypeError:
                    is_match = False

        return is_match

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return f"<DictMatching {self._values!r}>"


def DictMatching(values: Mapping[str, Any]) -> Any:
    """Match any dictionary with the passed in keys / values.

    Arguments:
        values: Keys and values to check.

    !!! example
        ```python
        value = {"hello": "world", "goodbye": "so long"}
        assert value == matchers.DictMatching({"hello": "world"})
        ```
    """
    return _DictMatching(values)


class _ListMatching:
    _values: List[Any]

    def __init__(self, values: List[Any]) -> None:
        self._values = values

    def __eq__(self, target: object) -> bool:
        """Return true if target matches all given values."""
        if not hasattr(target, "__iter__"):
            return False

        return all(
            any(item == target_item for target_item in target) for item in self._values
        )

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return f"<ListMatching {self._values!r}>"


def ListMatching(values: List[Any]) -> Any:
    """Match any list with the passed in values.

    Arguments:
        values: Values to check.

    !!! example
        ```python
        value = [1, 2, 3]
        assert value == matchers.ListMatching([1, 2])
        ```
    """
    return _ListMatching(values)


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
    _error_type: Type[BaseException]
    _string_matcher: Optional[_StringMatching]

    def __init__(self, error: Type[BaseException], match: Optional[str] = None) -> None:
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


def ErrorMatching(error: Type[ErrorT], match: Optional[str] = None) -> ErrorT:
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


class _Captor:
    def __init__(self) -> None:
        self._values: List[Any] = []

    def __eq__(self, target: object) -> bool:
        """Capture compared value, always returning True."""
        self._values.append(target)
        return True

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return "<Captor>"

    @property
    def value(self) -> Any:
        """Get the captured value.

        Raises:
            AssertionError: if no value was captured.
        """
        if len(self._values) == 0:
            raise AssertionError("No value captured by captor.")

        return self._values[-1]

    @property
    def values(self) -> List[Any]:
        """Get all captured values."""
        return self._values


def Captor() -> Any:
    """Match anything, capturing its value.

    The last captured value will be set to `captor.value`. All captured
    values will be placed in the `captor.values` list, which can be
    helpful if a captor needs to be triggered multiple times.

    !!! example
        ```python
        captor = Captor()
        assert "foobar" == captor
        print(captor.value)  # "foobar"
        print(captor.values)  # ["foobar"]
        ```
    """
    return _Captor()
