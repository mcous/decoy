"""Matcher helpers.

A "matcher" is a helper class with an `__eq__` method defined. Use them
anywhere in your test where you would use an actual value for equality
(`==`) comparision.

Matchers help you loosen assertions where strict adherence to an exact value
is not relevent to what you're trying to test.

Example:
    ```python
    from decoy import Decoy, matchers

    # ...

    def test_logger_called(decoy: Decoy):
        # ...
        decoy.verify(
            logger.log(msg=matchers.StringMatching("hello"))
        )
    ```

Note:
    Identity comparisons (`is`) will not work with matchers. Decoy only uses
    equality comparisons for stubbing and verification.
"""
from re import compile as compile_re
from typing import cast, Any, Optional, Pattern, Type


__all__ = [
    "Anything",
    "IsA",
    "IsNot",
    "StringMatching",
    "ErrorMatching",
]


class _Anything:
    def __eq__(self, target: object) -> bool:
        """Return true if target is not None."""
        return target is not None

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return "<Anything>"


def Anything() -> Any:
    """Match anything except None.

    Example:
        ```python
        assert "foobar" == Anything()
        assert None != Anything()
        ```
    """
    return _Anything()


class _IsA:
    _match_type: type

    def __init__(self, match_type: type) -> None:
        """Initialize the matcher with a type."""
        self._match_type = match_type

    def __eq__(self, target: object) -> bool:
        """Return true if target is a self._match_type."""
        return type(target) == self._match_type

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return "<IsA {self._match_type.__name__}>"


def IsA(match_type: type) -> Any:
    """Match anything that satisfies the passed in type.

    Arguments:
        match_type: Type to match.

    Example:
        ```python
        assert "foobar" == IsA(str)
        assert datetime.now() == IsA(datetime)
        assert 42 == IsA(int)
        ```
    """
    return _IsA(match_type)


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
        return f"<IsNot {self._reject_value}>"


def IsNot(value: object) -> Any:
    """Match anything that isn't the passed in value.

    Arguments:
        value: Value to check against.

    Example:
        ```python
        assert "foobar" == IsNot("bazquux")
        assert 42 == IsNot("the question")
        assert 1 != IsNot(1)
        ```
    """
    return _IsNot(value)


class _StringMatching:
    _pattern: Pattern[str]

    def __init__(self, match: str) -> None:
        """Initialize the matcher with the pattern to match."""
        self._pattern = compile_re(match)

    def __eq__(self, target: object) -> bool:
        """Return true if target is not self._reject_value."""
        return (
            type(target) is str and self._pattern.search(cast(str, target)) is not None
        )

    def __repr__(self) -> str:
        """Return a string representation of the matcher."""
        return f"<StringMatching {self._pattern.pattern}>"


def StringMatching(match: str) -> str:
    """Match any string matching the passed in pattern.

    Arguments:
        match: Pattern to check against; will be compiled into an re.Pattern.

    Example:
        ```python
        assert "foobar" == StringMatching("bar")
        assert "foobar" != StringMatching("^bar")
        ```
    """
    return cast(str, _StringMatching(match))


class _ErrorMatching:
    _error_type: Type[Exception]
    _string_matcher: Optional[_StringMatching]

    def __init__(self, error: Type[Exception], match: Optional[str] = None) -> None:
        """Initialize with the Exception type and optional message matcher."""
        self._error_type = error
        self._string_matcher = _StringMatching(match) if match is not None else None

    def __eq__(self, target: object) -> bool:
        """Return true if target is not self._reject_value."""
        error_match = type(target) == self._error_type
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


def ErrorMatching(error: Type[Exception], match: Optional[str] = None) -> Exception:
    """Match any error matching an Exception type and optional message matcher.

    Arguments:
        error: Exception type to match against.
        match: Pattern to check against; will be compiled into an re.Pattern.

    Example:
        ```python
        assert ValueError("oh no!") == ErrorMatching(ValueError)
        assert ValueError("oh no!") == ErrorMatching(ValueError, match="no")
        ```
    """
    return cast(Exception, _ErrorMatching(error, match))
