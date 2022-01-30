"""Tests for Spec instances."""
import pytest
import inspect
from typing import Any, Dict, NamedTuple, Optional, Tuple, Type

from decoy.spec import Spec, BoundArgs
from decoy.warnings import IncorrectCallWarning
from .common import (
    SomeClass,
    SomeAsyncClass,
    SomeAsyncCallableClass,
    SomeNestedClass,
    some_func,
    some_async_func,
)


def test_init() -> None:
    """It should have default spec properties."""
    subject = Spec(source=None, name=None)

    assert subject.get_signature() is None
    assert subject.get_class_type() is None
    assert subject.get_is_async() is False


class GetNameSpec(NamedTuple):
    """Spec data to test get_name and get_full_name."""

    subject: Spec
    expected_name: str
    expected_full_name: str


@pytest.mark.parametrize(
    GetNameSpec._fields,
    [
        GetNameSpec(
            subject=Spec(source=None, name=None),
            expected_name="unnamed",
            expected_full_name="unnamed",
        ),
        GetNameSpec(
            subject=Spec(source=some_func, name=None),
            expected_name="some_func",
            expected_full_name="tests.common.some_func",
        ),
        GetNameSpec(
            subject=Spec(source=some_func, name="spy_name", module_name="module_name"),
            expected_name="spy_name",
            expected_full_name="module_name.spy_name",
        ),
        GetNameSpec(
            subject=Spec(source=some_func, name="spy_name", module_name=None),
            expected_name="spy_name",
            expected_full_name="spy_name",
        ),
        GetNameSpec(
            subject=Spec(source=SomeClass, name=None).get_child_spec("foo"),
            expected_name="SomeClass.foo",
            expected_full_name="tests.common.SomeClass.foo",
        ),
        GetNameSpec(
            subject=(
                Spec(source=SomeNestedClass, name=None)
                .get_child_spec("child")
                .get_child_spec("foo")
            ),
            expected_name="SomeNestedClass.child.foo",
            expected_full_name="tests.common.SomeNestedClass.child.foo",
        ),
    ],
)
def test_get_name(subject: Spec, expected_name: str, expected_full_name: str) -> None:
    """It should assign names from args or spec."""
    assert subject.get_name() == expected_name
    assert subject.get_full_name() == expected_full_name


class GetSignatureSpec(NamedTuple):
    """Spec data to test get_signature."""

    subject: Spec
    expected_signature: Optional[inspect.Signature]


@pytest.mark.parametrize(
    GetSignatureSpec._fields,
    [
        GetSignatureSpec(
            subject=Spec(source=None, name=None),
            expected_signature=None,
        ),
        GetSignatureSpec(
            subject=Spec(source=some_func, name=None),
            expected_signature=inspect.Signature(
                parameters=[
                    inspect.Parameter(
                        name="val",
                        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=str,
                    )
                ],
                return_annotation=str,
            ),
        ),
        GetSignatureSpec(
            subject=Spec(source=SomeClass, name=None).get_child_spec("foo"),
            expected_signature=inspect.Signature(
                parameters=[
                    inspect.Parameter(
                        name="val",
                        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=str,
                    )
                ],
                return_annotation=str,
            ),
        ),
        GetSignatureSpec(
            subject=(
                Spec(source=SomeNestedClass, name=None)
                .get_child_spec("child")
                .get_child_spec("foo")
            ),
            expected_signature=inspect.Signature(
                parameters=[
                    inspect.Parameter(
                        name="val",
                        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=str,
                    )
                ],
                return_annotation=str,
            ),
        ),
        GetSignatureSpec(
            subject=(
                Spec(source=SomeNestedClass, name=None)
                .get_child_spec("child_attr")
                .get_child_spec("foo")
            ),
            expected_signature=inspect.Signature(
                parameters=[
                    inspect.Parameter(
                        name="val",
                        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=str,
                    )
                ],
                return_annotation=str,
            ),
        ),
        GetSignatureSpec(
            subject=Spec(source=SomeClass, name=None).get_child_spec("fizzbuzz"),
            expected_signature=inspect.Signature(
                parameters=[
                    inspect.Parameter(
                        name="hello",
                        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=str,
                    )
                ],
                return_annotation=int,
            ),
        ),
    ],
)
def test_get_signature(
    subject: Spec,
    expected_signature: Optional[inspect.Signature],
) -> None:
    """It should inspect the spec source's signature."""
    assert subject.get_signature() == expected_signature


@pytest.mark.filterwarnings("ignore:'NoneType' object is not subscriptable")
def test_get_signature_no_type_hints() -> None:
    """It should gracefully degrade if a class's type hints cannot be resolved."""

    class _BadTypeHints:
        _not_ok: "None[Any]"

        def _ok(self, hello: str) -> None:
            ...

    subject = Spec(source=_BadTypeHints, name=None).get_child_spec("_ok")

    assert subject.get_signature() == inspect.Signature(
        parameters=[
            inspect.Parameter(
                name="hello",
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=str,
            )
        ],
        return_annotation=None,
    )


class GetClassTypeSpec(NamedTuple):
    """Spec data to test get_class_type."""

    subject: Spec
    expected_class_type: Optional[Type[Any]]


@pytest.mark.parametrize(
    GetClassTypeSpec._fields,
    [
        GetClassTypeSpec(
            subject=Spec(source=None, name=None),
            expected_class_type=None,
        ),
        GetClassTypeSpec(
            subject=Spec(source=some_func, name=None),
            expected_class_type=None,
        ),
        GetClassTypeSpec(
            subject=Spec(source=SomeClass, name=None),
            expected_class_type=SomeClass,
        ),
    ],
)
def test_get_class_type(subject: Spec, expected_class_type: Type[Any]) -> None:
    """It should get the class type, if source is a class."""
    assert subject.get_class_type() == expected_class_type


class GetIsAsyncSpec(NamedTuple):
    """Spec data to test get_is_async."""

    subject: Spec
    expected_is_async: bool


@pytest.mark.parametrize(
    GetIsAsyncSpec._fields,
    [
        GetIsAsyncSpec(
            subject=Spec(source=None, name=None),
            expected_is_async=False,
        ),
        GetIsAsyncSpec(
            subject=Spec(source=some_func, name=None),
            expected_is_async=False,
        ),
        GetIsAsyncSpec(
            subject=Spec(source=SomeClass, name=None),
            expected_is_async=False,
        ),
        GetIsAsyncSpec(
            subject=Spec(source=some_async_func, name=None),
            expected_is_async=True,
        ),
        GetIsAsyncSpec(
            subject=Spec(source=SomeAsyncCallableClass, name=None),
            expected_is_async=True,
        ),
        GetIsAsyncSpec(
            subject=Spec(source=SomeAsyncClass, name=None).get_child_spec("foo"),
            expected_is_async=True,
        ),
    ],
)
def test_get_is_async(subject: Spec, expected_is_async: bool) -> None:
    """It should get whether the Spec represents an async callable."""
    assert subject.get_is_async() is expected_is_async


class GetBindArgsSpec(NamedTuple):
    """Spec data to test bind_args."""

    subject: Spec
    input_args: Tuple[Any, ...]
    input_kwargs: Dict[str, Any]
    expected_args: Tuple[Any, ...]
    expected_kwargs: Dict[str, Any]


@pytest.mark.parametrize(
    GetBindArgsSpec._fields,
    [
        GetBindArgsSpec(
            subject=Spec(source=None, name=None),
            input_args=(1, 2, 3),
            input_kwargs={"four": "five", "six": "seven"},
            expected_args=(1, 2, 3),
            expected_kwargs={"four": "five", "six": "seven"},
        ),
        GetBindArgsSpec(
            subject=Spec(source=some_func, name=None),
            input_args=(),
            input_kwargs={"val": "hello"},
            expected_args=("hello",),
            expected_kwargs={},
        ),
    ],
)
def test_bind_args(
    subject: Spec,
    input_args: Tuple[Any, ...],
    input_kwargs: Dict[str, Any],
    expected_args: Tuple[Any, ...],
    expected_kwargs: Dict[str, Any],
) -> None:
    """It should bind arguments to the spec's callable signature."""
    result = subject.bind_args(*input_args, **input_kwargs)

    assert result == BoundArgs(args=expected_args, kwargs=expected_kwargs)


def test_warn_if_called_incorrectly() -> None:
    """It should trigger a warning if bound_args is called incorrectly."""
    subject = Spec(source=some_func, name=None)

    with pytest.warns(IncorrectCallWarning, match="missing a required argument"):
        subject.bind_args(wrong_arg_name="1")
