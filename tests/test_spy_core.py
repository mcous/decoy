"""Tests for SpyCore instances."""
import pytest
import inspect
from typing import Any, Dict, NamedTuple, Optional, Tuple, Type

from decoy.spy_core import SpyCore, BoundArgs
from decoy.warnings import IncorrectCallWarning
from .fixtures import (
    SomeClass,
    SomeAsyncClass,
    SomeAsyncCallableClass,
    SomeCallableClass,
    SomeNestedClass,
    some_func,
    some_async_func,
    some_wrapped_func,
)


def test_init() -> None:
    """It should have default spec properties."""
    subject = SpyCore(source=None, name=None)

    assert isinstance(subject.info.id, int)
    assert subject.signature is None
    assert subject.class_type is None
    assert subject.is_async is False

    assert subject.info.id != SpyCore(source=None, name=None).info.id


class GetNameSpec(NamedTuple):
    """Spec data to test info and full_name."""

    subject: SpyCore
    expected_name: str
    expected_full_name: str


@pytest.mark.parametrize(
    GetNameSpec._fields,
    [
        GetNameSpec(
            subject=SpyCore(source=None, name=None),
            expected_name="unnamed",
            expected_full_name="unnamed",
        ),
        GetNameSpec(
            subject=SpyCore(source=some_func, name=None),
            expected_name="some_func",
            expected_full_name="tests.fixtures.some_func",
        ),
        GetNameSpec(
            subject=SpyCore(
                source=some_func, name="spy_name", module_name="module_name"
            ),
            expected_name="spy_name",
            expected_full_name="module_name.spy_name",
        ),
        GetNameSpec(
            subject=SpyCore(source=some_func, name="spy_name", module_name=None),
            expected_name="spy_name",
            expected_full_name="spy_name",
        ),
        GetNameSpec(
            subject=SpyCore(source=SomeClass, name=None).create_child_core(
                "foo", is_async=False
            ),
            expected_name="SomeClass.foo",
            expected_full_name="tests.fixtures.SomeClass.foo",
        ),
        GetNameSpec(
            subject=(
                SpyCore(source=SomeNestedClass, name=None)
                .create_child_core("child", is_async=False)
                .create_child_core("foo", is_async=False)
            ),
            expected_name="SomeNestedClass.child.foo",
            expected_full_name="tests.fixtures.SomeNestedClass.child.foo",
        ),
    ],
)
def test_get_name(
    subject: SpyCore, expected_name: str, expected_full_name: str
) -> None:
    """It should assign names from args or spec."""
    assert subject.info.name == expected_name
    assert subject.full_name == expected_full_name


class GetSignatureSpec(NamedTuple):
    """Spec data to test get_signature."""

    subject: SpyCore
    expected_signature: Optional[inspect.Signature]


@pytest.mark.parametrize(
    GetSignatureSpec._fields,
    [
        GetSignatureSpec(
            subject=SpyCore(source=None, name=None),
            expected_signature=None,
        ),
        GetSignatureSpec(
            subject=SpyCore(source=some_func, name=None),
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
            subject=SpyCore(source=SomeClass, name=None).create_child_core(
                "foo", is_async=False
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
            subject=SpyCore(source=SomeClass, name=None).create_child_core(
                "primitive_property", is_async=False
            ),
            expected_signature=None,
        ),
        GetSignatureSpec(
            subject=(
                SpyCore(source=SomeNestedClass, name=None)
                .create_child_core("child", is_async=False)
                .create_child_core("foo", is_async=False)
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
                SpyCore(source=SomeNestedClass, name=None)
                .create_child_core("child_attr", is_async=False)
                .create_child_core("foo", is_async=False)
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
            subject=SpyCore(source=SomeClass, name=None).create_child_core(
                "fizzbuzz", is_async=False
            ),
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
        GetSignatureSpec(
            subject=SpyCore(source=SomeCallableClass, name=None),
            expected_signature=inspect.Signature(
                parameters=[
                    inspect.Parameter(
                        name="val",
                        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=int,
                    )
                ],
                return_annotation=int,
            ),
        ),
        GetSignatureSpec(
            subject=SpyCore(source=some_wrapped_func, name=None),
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
            subject=SpyCore(source=SomeClass, name=None).create_child_core(
                "some_wrapped_method", is_async=False
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
    ],
)
def test_get_signature(
    subject: SpyCore,
    expected_signature: Optional[inspect.Signature],
) -> None:
    """It should inspect the spec source's signature."""
    assert subject.signature == expected_signature


@pytest.mark.filterwarnings("ignore:'NoneType' object is not subscriptable")
def test_get_signature_no_type_hints() -> None:
    """It should gracefully degrade if a class's type hints cannot be resolved."""

    class _BadTypeHints:
        _not_ok: "None[Any]"

        def _ok(self, hello: str) -> None:
            ...

    subject = SpyCore(source=_BadTypeHints, name=None).create_child_core(
        "_ok", is_async=False
    )

    assert subject.signature == inspect.Signature(
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

    subject: SpyCore
    expected_class_type: Optional[Type[Any]]


@pytest.mark.parametrize(
    GetClassTypeSpec._fields,
    [
        GetClassTypeSpec(
            subject=SpyCore(source=None, name=None),
            expected_class_type=None,
        ),
        GetClassTypeSpec(
            subject=SpyCore(source=some_func, name=None),
            expected_class_type=None,
        ),
        GetClassTypeSpec(
            subject=SpyCore(source=SomeClass, name=None),
            expected_class_type=SomeClass,
        ),
    ],
)
def test_get_class_type(subject: SpyCore, expected_class_type: Type[Any]) -> None:
    """It should get the class type, if source is a class."""
    assert subject.class_type == expected_class_type


class GetIsAsyncSpec(NamedTuple):
    """Spec data to test get_is_async."""

    subject: SpyCore
    expected_is_async: bool


@pytest.mark.parametrize(
    GetIsAsyncSpec._fields,
    [
        GetIsAsyncSpec(
            subject=SpyCore(source=None, name=None),
            expected_is_async=False,
        ),
        GetIsAsyncSpec(
            subject=SpyCore(source=None, name=None, is_async=True),
            expected_is_async=True,
        ),
        GetIsAsyncSpec(
            subject=SpyCore(source=some_func, name=None),
            expected_is_async=False,
        ),
        GetIsAsyncSpec(
            subject=SpyCore(source=SomeClass, name=None),
            expected_is_async=False,
        ),
        GetIsAsyncSpec(
            subject=SpyCore(source=some_async_func, name=None),
            expected_is_async=True,
        ),
        GetIsAsyncSpec(
            subject=SpyCore(source=SomeAsyncCallableClass, name=None),
            expected_is_async=True,
        ),
        GetIsAsyncSpec(
            subject=SpyCore(source=SomeAsyncClass, name=None).create_child_core(
                "foo", is_async=False
            ),
            expected_is_async=True,
        ),
        GetIsAsyncSpec(
            subject=SpyCore(source=None, name=None).create_child_core(
                "foo", is_async=True
            ),
            expected_is_async=True,
        ),
    ],
)
def test_get_is_async(subject: SpyCore, expected_is_async: bool) -> None:
    """It should get whether the Spec represents an async callable."""
    assert subject.is_async is expected_is_async


class GetBindArgsSpec(NamedTuple):
    """Spec data to test bind_args."""

    subject: SpyCore
    input_args: Tuple[Any, ...]
    input_kwargs: Dict[str, Any]
    expected_args: Tuple[Any, ...]
    expected_kwargs: Dict[str, Any]


@pytest.mark.parametrize(
    GetBindArgsSpec._fields,
    [
        GetBindArgsSpec(
            subject=SpyCore(source=None, name=None),
            input_args=(1, 2, 3),
            input_kwargs={"four": "five", "six": "seven"},
            expected_args=(1, 2, 3),
            expected_kwargs={"four": "five", "six": "seven"},
        ),
        GetBindArgsSpec(
            subject=SpyCore(source=some_func, name=None),
            input_args=(),
            input_kwargs={"val": "hello"},
            expected_args=("hello",),
            expected_kwargs={},
        ),
        GetBindArgsSpec(
            subject=SpyCore(source=some_wrapped_func, name=None),
            input_args=(),
            input_kwargs={"val": "hello"},
            expected_args=("hello",),
            expected_kwargs={},
        ),
    ],
)
def test_bind_args(
    subject: SpyCore,
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
    subject = SpyCore(source=some_func, name=None)

    with pytest.warns(IncorrectCallWarning, match="missing a required argument"):
        subject.bind_args(wrong_arg_name="1")
