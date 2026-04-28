"""Migration codemod tests."""

import sys

import pytest
from libcst.codemod import CodemodTest

if sys.version_info >= (3, 10):
    from decoy.codemods.migrate import MigrateCommand
else:
    MigrateCommand = None

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="v3 preview only supports Python >= 3.10",
)


class TestMigrateCommand(CodemodTest):
    """Tests for decoy.codemods.migrate."""

    TRANSFORM = MigrateCommand

    def test_import_decoy(self) -> None:
        """Swap to `decoy.next` for main Decoy."""
        before = """
            from decoy import Decoy
        """
        after = """
            from decoy.next import Decoy
        """

        self.assertCodemod(before, after)

    def test_import_decoy_star(self) -> None:
        """Leave import star alone, since it would be too complicated to migrate."""
        before = """
            from decoy import *
        """
        after = """
            from decoy import *
        """

        self.assertCodemod(before, after)

    def test_import_decoy_errors_and_warnings(self) -> None:
        """Keep to errors and warnings from regular `decoy`."""
        before = """
            from decoy import Decoy, Stub, errors, warnings
        """
        after = """
            from decoy import errors, warnings
            from decoy.next import Decoy, Stub
        """

        self.assertCodemod(before, after)

    def test_import_remove_prop(self) -> None:
        """Remove `Prop` import."""
        before = """
            from decoy import Prop
        """
        after = ""

        self.assertCodemod(before, after)

    def test_import_rename_matcher(self) -> None:
        """Swap `matchers` to `Matcher` from `decoy.next`."""
        before = """
            from decoy import Decoy, matchers
        """
        after = """
            from decoy.next import Decoy, Matcher
        """

        self.assertCodemod(before, after)

    def test_when_called_with(self) -> None:
        """Swap when function rehearsal with `called_with`."""
        before = """
            decoy.when(some_func("hello", "world")).then_return(True)
        """
        after = """
            decoy.when(some_func).called_with("hello", "world").then_return(True)
        """

        self.assertCodemod(before, after)

    def test_when_called_with_on_self(self) -> None:
        """Swap when function rehearsal with `called_with` from `self._decoy`."""
        before = """
            self._decoy.when(some_func("hello", "world")).then_return(True)
            self.decoy.when(some_func("hello", "world")).then_return(True)
        """
        after = """
            self._decoy.when(some_func).called_with("hello", "world").then_return(True)
            self.decoy.when(some_func).called_with("hello", "world").then_return(True)
        """

        self.assertCodemod(before, after)

    def test_when_called_with_idempotent(self) -> None:
        """Does not touch `called_with` twice."""
        before = """
            decoy.when(some.func).called_with("hello").then_return(True)
            decoy.when(some.func).get().then_return(True)
            decoy.when(some.func).set("hello").then_raise(RuntimeError())
            decoy.when(some.func).delete().then_raise(RuntimeError())
        """
        after = """
            decoy.when(some.func).called_with("hello").then_return(True)
            decoy.when(some.func).get().then_return(True)
            decoy.when(some.func).set("hello").then_raise(RuntimeError())
            decoy.when(some.func).delete().then_raise(RuntimeError())
        """

        self.assertCodemod(before, after)

    def test_when_called_with_extra_args(self) -> None:
        """Swap when function rehearsal with `called_with`, keeping extra args."""
        before = """
            decoy.when(some_func("hello"), ignore_extra_args=True).then_return(True)
        """
        after = """
            decoy.when(some_func, ignore_extra_args=True).called_with("hello").then_return(True)
        """

        self.assertCodemod(before, after)

    def test_when_attribute_get(self) -> None:
        """Swap attribute get rehearsal with `get`."""
        before = """
            decoy.when(mock.some_prop).then_return(True)
        """
        after = """
            decoy.when(mock.some_prop).get().then_return(True)
        """

        self.assertCodemod(before, after)

    def test_when_attribute_set(self) -> None:
        """Swap attribute set rehearsal with `set`."""
        before = """
            decoy.when(decoy.prop(mock.some_prop).set(42)).then_raise(RuntimeError("oh no"))
        """
        after = """
            decoy.when(mock.some_prop).set(42).then_raise(RuntimeError("oh no"))
        """

        self.assertCodemod(before, after)

    def test_when_attribute_delete(self) -> None:
        """Swap attribute delete rehearsal with `delete`."""
        before = """
            decoy.when(decoy.prop(mock.some_prop).delete()).then_raise(RuntimeError("oh no"))
        """
        after = """
            decoy.when(mock.some_prop).delete().then_raise(RuntimeError("oh no"))
        """

        self.assertCodemod(before, after)

    def test_verify_called_with(self) -> None:
        """Swap verify function rehearsal with `called_with`."""
        before = """
            decoy.verify(some_func("hello", "world"))
        """
        after = """
            decoy.verify(some_func).called_with("hello", "world")
        """

        self.assertCodemod(before, after)

    def test_verify_called_with_on_self(self) -> None:
        """Swap when function rehearsal with `called_with` from `self._decoy`."""
        before = """
            self._decoy.verify(some_func("hello", "world"))
            self.decoy.verify(some_func("hello", "world"))
        """
        after = """
            self._decoy.verify(some_func).called_with("hello", "world")
            self.decoy.verify(some_func).called_with("hello", "world")
        """

        self.assertCodemod(before, after)

    def test_verify_called_with_extra_args(self) -> None:
        """Swap verify function rehearsal with `called_with`, keeping extra args."""
        before = """
            decoy.verify(some_func("hello"), times=1)
        """
        after = """
            decoy.verify(some_func, times=1).called_with("hello")
        """

        self.assertCodemod(before, after)

    def test_verify_order(self) -> None:
        """Swap multiple rehearsals in `verify` for `verify_order`."""
        before = """
            decoy.verify(
                some_func("hello"),
                other_func("world"),
            )
        """
        after = """
            with decoy.verify_order():
                decoy.verify(some_func).called_with("hello")
                decoy.verify(other_func).called_with("world")
        """

        self.assertCodemod(before, after)

    def test_verify_order_on_self(self) -> None:
        """Swap multiple rehearsals in `verify` for `verify_order` on `self`."""
        before = """
            self.decoy.verify(
                some_func("hello"),
                other_func("world"),
            )
            self._decoy.verify(
                some_func("hello"),
                other_func("world"),
            )
        """
        after = """
            with self.decoy.verify_order():
                self.decoy.verify(some_func).called_with("hello")
                self.decoy.verify(other_func).called_with("world")
            with self._decoy.verify_order():
                self._decoy.verify(some_func).called_with("hello")
                self._decoy.verify(other_func).called_with("world")
        """

        self.assertCodemod(before, after)

    def test_verify_order_attributes(self) -> None:
        """Swaps multiple attribute rehearsals in `verify` for `verify_order`."""
        before = """
            decoy.verify(
                decoy.prop(some.attr).set("hello"),
                other_func("world"),
            )
        """
        after = """
            with decoy.verify_order():
                decoy.verify(some.attr).set("hello")
                decoy.verify(other_func).called_with("world")
        """

        self.assertCodemod(before, after)

    def test_verify_order_kwargs(self) -> None:
        """Copies kwargs to each verify."""
        before = """
            decoy.verify(
                some_func("hello"),
                other_func("world"),
                times=1,
            )
        """
        after = """
            with decoy.verify_order():
                decoy.verify(some_func, times=1).called_with("hello")
                decoy.verify(other_func, times=1).called_with("world")
        """

        self.assertCodemod(before, after)

    def test_verify_order_spread(self) -> None:
        """It migrates conditional spreads in a verify order."""
        before = """
            decoy.verify(
                some_func("hello"),
                *(
                    some_flag
                    and [
                      other_func("world"),
                      another_func("fizzbuzz"),
                    ]
                    or []
                )
            )
        """
        after = """
            with decoy.verify_order():
                decoy.verify(some_func).called_with("hello")
                if some_flag:
                    decoy.verify(other_func).called_with("world")
                    decoy.verify(another_func).called_with("fizzbuzz")
        """

        self.assertCodemod(before, after)

    def test_whitespace(self) -> None:
        """It clears out whitespace and commas."""
        before = """
            decoy.when(
                mock(
                    some_arg="some-value",
                )
            ).then_return("some-result")
        """
        after = """
            decoy.when(mock).called_with(some_arg="some-value").then_return("some-result")
        """

        self.assertCodemod(before, after)

    def test_async(self) -> None:
        """It migrates async rehearsals."""
        before = """
            decoy.when(await mock("hello")).then_return("world")
            decoy.verify(await mock("hello"))
        """
        after = """
            decoy.when(mock).called_with("hello").then_return("world")
            decoy.verify(mock).called_with("hello")
        """

        self.assertCodemod(before, after)

    def test_async_verify_order(self) -> None:
        """Swap multiple async rehearsals in `verify` for `verify_order`."""
        before = """
            decoy.verify(
                await some_func("hello"),
                await other_func("world"),
            )
        """
        after = """
            with decoy.verify_order():
                decoy.verify(some_func).called_with("hello")
                decoy.verify(other_func).called_with("world")
        """

        self.assertCodemod(before, after)

    def test_migrate_matcher_in_call(self) -> None:
        """Migrates `matchers` to type-safe `Matcher` in a call."""
        cases = [
            (
                "matchers.AnythingOrNone()",
                "Matcher.any()",
            ),
            (
                'matchers.HasAttributes({"hello": "world"})',
                'Matcher.any(attrs={"hello": "world"})',
            ),
            (
                'matchers.HasAttributes(attributes={"hello": "world"})',
                'Matcher.any(attrs={"hello": "world"})',
            ),
            (
                "matchers.IsA(HelloWorld)",
                "Matcher.any(HelloWorld)",
            ),
            (
                "matchers.IsA(match_type=HelloWorld)",
                "Matcher.any(type=HelloWorld)",
            ),
            (
                'matchers.IsA(HelloWorld, {"hello": "world"})',
                'Matcher.any(HelloWorld, {"hello": "world"})',
            ),
            (
                'matchers.IsA(match_type=HelloWorld, attributes={"hello": "world"})',
                'Matcher.any(type=HelloWorld, attrs={"hello": "world"})',
            ),
            (
                'matchers.DictMatching({"hello": "world"})',
                'Matcher.contains({"hello": "world"})',
            ),
            (
                'matchers.ListMatching(["hello", "world"])',
                'Matcher.contains(["hello", "world"])',
            ),
            (
                "matchers.ErrorMatching(HelloWorldError)",
                "Matcher.error(HelloWorldError)",
            ),
            (
                "matchers.ErrorMatching(error=HelloWorldError)",
                "Matcher.error(type=HelloWorldError)",
            ),
            (
                'matchers.ErrorMatching(HelloWorldError, "hello world")',
                'Matcher.error(HelloWorldError, "hello world")',
            ),
            (
                'matchers.ErrorMatching(error=HelloWorldError, match="hello world")',
                'Matcher.error(type=HelloWorldError, match="hello world")',
            ),
            (
                'matchers.IsNot("hello world")',
                'Matcher.is_not("hello world")',
            ),
            (
                "matchers.Anything()",
                "Matcher.is_not(None)",
            ),
            (
                'matchers.StringMatching("hello world")',
                'Matcher.matches("hello world")',
            ),
        ]

        for before, after in cases:
            self.assertCodemod(
                f"""
                    mock({before})
                """,
                f"""
                    mock({after}.arg)
                """,
            )

    def test_migrate_unknown_matcher_in_arg_noop(self) -> None:
        """It leaves unknown matchers alone inside function args."""
        before = """
            mock(matchers.FizzBuzz())
        """
        after = """
            mock(matchers.FizzBuzz())
        """

        self.assertCodemod(before, after)

    def test_migrate_isa_only_attrs_kwarg(self) -> None:
        """It correctly maps IsA when only attributes kwarg is provided."""
        self.assertCodemod(
            """
                mock(matchers.IsA(attributes={"hello": "world"}))
            """,
            """
                mock(Matcher.any(attrs={"hello": "world"}).arg)
            """,
        )

    def test_migrate_isa_kwargs_reversed(self) -> None:
        """It correctly remaps IsA kwargs regardless of order."""
        self.assertCodemod(
            """
                mock(matchers.IsA(attributes={"hello": "world"}, match_type=HelloWorld))
            """,
            """
                mock(Matcher.any(type=HelloWorld, attrs={"hello": "world"}).arg)
            """,
        )

    def test_migrate_error_matching_kwargs_reversed(self) -> None:
        """It correctly remaps ErrorMatching kwargs regardless of order."""
        self.assertCodemod(
            """
                mock(matchers.ErrorMatching(match="hello world", error=HelloWorldError))
            """,
            """
                mock(Matcher.error(type=HelloWorldError, match="hello world").arg)
            """,
        )

    def test_migrate_matcher_with_other_args(self) -> None:
        """It migrates all args that are matchers."""
        before = """
            mock("hello", matchers.AnythingOrNone())
        """
        after = """
            mock("hello", Matcher.any().arg)
        """

        self.assertCodemod(before, after)

    def test_migrate_matcher_standalone(self) -> None:
        """It migrates matchers in standalone usage."""
        before = """
            assert "hello" == matchers.AnythingOrNone()
        """
        after = """
            assert "hello" == Matcher.any()
        """

        self.assertCodemod(before, after)

    def test_migrate_matcher_call_in_collection(self) -> None:
        """It migrates matchers in standalone usage."""
        before = """
            mock([matchers.AnythingOrNone()])
            mock((matchers.AnythingOrNone(),))
        """
        after = """
            mock([Matcher.any().arg])
            mock((Matcher.any().arg,))
        """

        self.assertCodemod(before, after)

    def test_migrate_legacy_captor(self) -> None:
        """It migrates legacy captor matchers."""
        before = """
            def test_one():
                captor = matchers.Captor()
                mock("hello", captor)

            def test_two():
                captor = SomethingElse()
                mock("hello", captor)
        """
        after = """
            def test_one():
                captor = Matcher.any()
                mock("hello", captor.arg)

            def test_two():
                captor = SomethingElse()
                mock("hello", captor)
        """

        self.assertCodemod(before, after)

    def test_migrate_value_captor(self) -> None:
        """It migrates newer, type-safe `ValueCaptor` matcher."""
        before = """
            def test_one():
                captor = matchers.ValueCaptor()
                mock("hello", captor.matcher)

            def test_two():
                captor = SomethingElse()
                mock("hello", captor)
        """
        after = """
            def test_one():
                captor = Matcher.any()
                mock("hello", captor.arg)

            def test_two():
                captor = SomethingElse()
                mock("hello", captor)
        """

        self.assertCodemod(before, after)

    def test_verify_order_spread_async(self) -> None:
        """It migrates async calls in conditional spreads."""
        before = """
            decoy.verify(
                some_func("hello"),
                *(
                    some_flag
                    and [
                      await other_func("world"),
                    ]
                    or []
                )
            )
        """
        after = """
            with decoy.verify_order():
                decoy.verify(some_func).called_with("hello")
                if some_flag:
                    decoy.verify(other_func).called_with("world")
        """

        self.assertCodemod(before, after)

    def test_verify_order_spread_nonempty_fallback(self) -> None:
        """It migrates conditional spreads with a non-empty fallback list."""
        before = """
            decoy.verify(
                some_func("hello"),
                *(
                    some_flag
                    and [other_func("world")]
                    or [fallback_func("fizzbuzz")]
                )
            )
        """
        after = """
            with decoy.verify_order():
                decoy.verify(some_func).called_with("hello")
                if some_flag:
                    decoy.verify(other_func).called_with("world")
                else:
                    decoy.verify(fallback_func).called_with("fizzbuzz")
        """

        self.assertCodemod(before, after)

    def test_migrate_captor_non_name_target(self) -> None:
        """It skips captor tracking for non-name assignment targets."""
        before = """
            self.captor = matchers.Captor()
            mock("hello", self.captor)
        """
        after = """
            self.captor = Matcher.any()
            mock("hello", self.captor)
        """

        self.assertCodemod(before, after)

    def test_migrate_captor_multiple_assignments_in_scope(self) -> None:
        """It identifies a captor among multiple assignments in scope."""
        before = """
            def test_one():
                other_var = 42
                captor = matchers.Captor()
                mock("hello", captor)
        """
        after = """
            def test_one():
                other_var = 42
                captor = Matcher.any()
                mock("hello", captor.arg)
        """

        self.assertCodemod(before, after)

    def test_migrate_unknown_matcher_noop(self) -> None:
        """It leaves unknown matchers alone."""
        before = """
            assert "hello" == matchers.FizzBuzz()
        """
        after = """
            assert "hello" == matchers.FizzBuzz()
        """

        self.assertCodemod(before, after)
