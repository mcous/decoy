"""Migrate Decoy v2 usage to the v3 API."""

from __future__ import annotations

import enum
from typing import Sequence, cast

import libcst as cst
from libcst import matchers as m
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.metadata import (
    Assignment,
    BaseAssignment,
    ParentNodeProvider,
    Scope,
    ScopeProvider,
)


class ImportAction(str, enum.Enum):
    """Import migration type."""

    KEEP = "keep"
    NEXT = "next"
    REMOVE = "remove"


IMPORT_MIGRATIONS = {
    "Decoy": ImportAction.NEXT,
    "Prop": ImportAction.REMOVE,
    "Stub": ImportAction.NEXT,
    "errors": ImportAction.KEEP,
    "warnings": ImportAction.KEEP,
    "matchers": ImportAction.NEXT,
}

IMPORT_RENAMES = {"matchers": "Matcher"}


class MigrateCommand(VisitorBasedCodemodCommand):
    """Codemod to migrate to Decoy v3.

    Only transforms calls on variables named `decoy`, `self.decoy`, or
    `self._decoy`. Tests using a different variable name will need manual migration.

    Only transforms matcher calls on the name `matchers`. Code using
    `from decoy import matchers as m` will need manual migration.

    Captor variables are migrated by name within their scope. If a captor variable
    is rebound to a non-captor value, uses after the rebinding will still be
    incorrectly migrated with `.arg`.
    """

    DESCRIPTION: str = "Migrate from Decoy v2 to Decoy v3 preview."

    METADATA_DEPENDENCIES = (ParentNodeProvider, ScopeProvider)

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)
        self._captor_assignments: set[BaseAssignment] = set()

    @m.leave(
        m.SimpleStatementLine(
            body=[
                m.ImportFrom(
                    module=m.Name("decoy"),
                    names=m.DoesNotMatch(m.ImportStar()),
                )
            ]
        )
    )
    def migrate_import(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> cst.SimpleStatementLine:
        """Transform import statements from `decoy` to `decoy.next`."""
        import_node = cst.ensure_type(updated_node.body[0], cst.ImportFrom)
        import_aliases = cast(Sequence[cst.ImportAlias], import_node.names)

        keep_imports = [
            _migrate_alias(a, rename=False)
            for a in import_aliases
            if _import_action(a) == ImportAction.KEEP
        ]
        next_imports = [
            _migrate_alias(a)
            for a in import_aliases
            if _import_action(a) == ImportAction.NEXT
        ]

        result: list[cst.SimpleStatementLine] = []

        if keep_imports:
            result.append(
                cst.SimpleStatementLine(
                    body=[import_node.with_changes(names=keep_imports)]
                )
            )

        if next_imports:
            result.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.ImportFrom(
                            module=cst.Attribute(
                                value=cst.Name("decoy"), attr=cst.Name("next")
                            ),
                            names=next_imports,
                        )
                    ]
                )
            )

        return cast(cst.SimpleStatementLine, cst.FlattenSentinel(result))

    @m.leave(
        m.SimpleStatementLine(
            body=[
                m.Expr(
                    value=m.Call(
                        func=m.Attribute(
                            value=(
                                m.Name("decoy")
                                | m.Attribute(
                                    value=m.Name("self"),
                                    attr=(m.Name("decoy") | m.Name("_decoy")),
                                )
                            ),
                            attr=m.Name("verify"),
                        ),
                        args=[
                            m.AtLeastN(
                                n=2,
                                matcher=(
                                    m.Arg(
                                        m.Call()
                                        | m.Attribute()
                                        | m.Await(m.Call() | m.Attribute())
                                    )
                                    | m.Arg(
                                        m.BooleanOperation(
                                            left=m.BooleanOperation(
                                                left=m.DoNotCare(),  # condition
                                                operator=m.And(),
                                                right=m.List(),  # true branch
                                            ),
                                            operator=m.Or(),
                                            right=m.List(),  # false branch
                                        ),
                                        star="*",
                                    )
                                ),
                            ),
                            m.ZeroOrMore(
                                m.Arg(
                                    keyword=(
                                        m.Name("times") | m.Name("ignore_extra_args")
                                    )
                                )
                            ),
                        ],
                    )
                )
            ]
        )
    )
    def migrate_verify_order(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> cst.SimpleStatementLine | cst.With:
        """Transform multiple verify calls into verify_order context."""
        expr = cst.ensure_type(updated_node.body[0], cst.Expr)
        call = cst.ensure_type(expr.value, cst.Call)
        attr = cst.ensure_type(call.func, cst.Attribute)

        kwargs = [arg for arg in call.args if arg.keyword]

        verify_statements: list[cst.BaseStatement] = [
            _extract_conditional_starred_arg(arg.value, attr, kwargs)
            if arg.star == "*"
            else cst.SimpleStatementLine(
                body=[cst.Expr(_migrate_rehearsal_stmt(attr, arg.value, kwargs))]
            )
            for arg in call.args
            if not arg.keyword
        ]

        verify_order_call = cst.Call(
            func=cst.Attribute(value=attr.value, attr=cst.Name("verify_order")),
            args=[],
        )

        return cst.With(
            items=[cst.WithItem(item=verify_order_call)],
            body=cst.IndentedBlock(body=verify_statements),
        )

    @m.leave(
        m.Call(
            func=m.Attribute(
                value=(
                    m.Name("decoy")
                    | m.Attribute(
                        value=m.Name("self"),
                        attr=(m.Name("decoy") | m.Name("_decoy")),
                    )
                ),
                attr=(m.Name("when") | m.Name("verify")),
            ),
            args=[
                m.Arg(m.Call() | m.Attribute() | m.Await(m.Call() | m.Attribute())),
                m.ZeroOrMore(
                    m.Arg(keyword=(m.Name("times") | m.Name("ignore_extra_args")))
                ),
            ],
        )
    )
    def migrate_call(
        self,
        original_node: cst.Call,
        updated_node: cst.Call,
    ) -> cst.Call:
        """Transform `decoy.when` and `decoy.verify` calls.

        - `decoy.when(some_func(...))` -> `decoy.when(some_func).called_with(...)`
        - `decoy.when(some.attr)` -> `decoy.when(some.attr).get()`
        - `decoy.verify(some_func(...))` -> `decoy.verify(some_func).called_with(...)`
        """
        parent = self.get_metadata(ParentNodeProvider, original_node)

        if m.matches(
            parent,  # pyright: ignore[reportArgumentType]
            m.Attribute(
                attr=(
                    m.Name("called_with")
                    | m.Name("get")
                    | m.Name("set")
                    | m.Name("delete")
                )
            ),
        ):
            return updated_node

        rehearsal = updated_node.args[0].value
        kwargs = updated_node.args[1:]

        if m.matches(rehearsal, m.Await()):
            rehearsal = cst.ensure_type(rehearsal, cst.Await).expression

        if m.matches(rehearsal, m.Attribute()):
            return cst.Call(
                func=cst.Attribute(value=updated_node, attr=cst.Name("get")),
                args=[],
            )

        rehearsal = cst.ensure_type(rehearsal, cst.Call)

        return _migrate_rehearsal(updated_node.func, rehearsal, kwargs)

    @m.call_if_inside(m.Arg())
    @m.leave(m.Call(func=m.Attribute(value=m.Name("matchers"))))
    def migrate_matcher_arg(
        self,
        original_node: cst.Call,
        updated_node: cst.Call,
    ) -> cst.Attribute | cst.Call:
        """Replace args using `matchers` with `Matcher` static methods."""
        migrated = _migrate_matcher(updated_node)
        if migrated is updated_node:
            return updated_node
        return cst.Attribute(value=migrated, attr=cst.Name("arg"))

    @m.call_if_not_inside(m.Arg())
    @m.leave(m.Call(func=m.Attribute(value=m.Name("matchers"))))
    def migrate_matcher_call(
        self,
        original_node: cst.Call,
        updated_node: cst.Call,
    ) -> cst.Call:
        """Replace args using `matchers` with `Matcher` static methods."""
        return _migrate_matcher(updated_node)

    @m.visit(
        m.Assign(
            value=m.Call(
                func=m.Attribute(
                    value=m.Name("matchers"),
                    attr=(m.Name("Captor") | m.Name("ValueCaptor")),
                )
            )
        )
    )
    def track_captor_assignment(self, node: cst.Assign) -> None:
        """Find captor assignments to add `.arg`."""
        scope = self._get_scope(node)
        target_node_ids = {
            id(target.target)
            for target in node.targets
            if m.matches(target.target, m.Name())
        }
        self._captor_assignments.update(
            a
            for a in scope.assignments  # pyright: ignore[reportAttributeAccessIssue]
            if isinstance(a, Assignment) and id(a.node) in target_node_ids
        )

    @m.leave(
        m.Arg(value=(m.Name() | m.Attribute(value=m.Name(), attr=m.Name("matcher"))))
    )
    def migrate_captor_arg(
        self,
        original_node: cst.Arg,
        updated_node: cst.Arg,
    ) -> cst.Arg:
        """Add `.arg` when captor is used as function argument."""
        name_node = (
            cst.ensure_type(original_node.value, cst.Attribute).value
            if m.matches(original_node.value, m.Attribute())
            else original_node.value
        )
        updated_name_node = (
            cst.ensure_type(updated_node.value, cst.Attribute).value
            if m.matches(updated_node.value, m.Attribute())
            else updated_node.value
        )

        name = cst.ensure_type(name_node, cst.Name).value
        scope = self._get_scope(original_node.value)

        if name in scope and any(  # pyright: ignore[reportOperatorIssue]
            a in self._captor_assignments
            for a in scope[name]  # pyright: ignore[reportIndexIssue]
        ):
            return updated_node.with_changes(
                value=cst.Attribute(value=updated_name_node, attr=cst.Name("arg"))
            )

        return updated_node

    def _get_scope(self, node: cst.CSTNode) -> Scope:
        scope = self.get_metadata(ScopeProvider, node)
        assert isinstance(scope, Scope)
        return scope


def _import_action(alias: cst.ImportAlias) -> ImportAction | None:
    action = IMPORT_MIGRATIONS.get(alias.evaluated_name)
    # matchers with an alias won't be fully migrated (matcher visitors hardcode
    # the name `matchers`), so keep it in `decoy` to fail loudly in v3
    if (
        action == ImportAction.NEXT
        and alias.evaluated_name == "matchers"
        and alias.asname is not None
    ):
        return ImportAction.KEEP
    return action


def _migrate_alias(alias: cst.ImportAlias, rename: bool = True) -> cst.ImportAlias:
    new_name = IMPORT_RENAMES.get(alias.evaluated_name) if rename else None
    return alias.with_changes(
        name=cst.Name(new_name) if new_name else alias.name,
        comma=cst.MaybeSentinel.DEFAULT,
    )


def _migrate_rehearsal(
    decoy_method: cst.BaseExpression,
    rehearsal: cst.Call,
    kwargs: Sequence[cst.Arg],
) -> cst.Call:
    if m.matches(
        rehearsal,
        m.Call(
            func=m.Attribute(
                value=m.Call(
                    func=m.Attribute(
                        value=(
                            m.Name("decoy")
                            | m.Attribute(
                                value=m.Name("self"),
                                attr=(m.Name("decoy") | m.Name("_decoy")),
                            )
                        ),
                        attr=m.Name("prop"),
                    ),
                    args=[m.Arg(value=m.DoNotCare())],
                ),
                attr=(m.Name("set") | m.Name("delete")),
            ),
            args=[m.ZeroOrOne(m.DoNotCare())],
        ),
    ):
        attribute_rehearsal = cst.ensure_type(rehearsal.func, cst.Attribute)
        prop_call = cst.ensure_type(attribute_rehearsal.value, cst.Call)
        mock = prop_call.args[0].value
        match_method = attribute_rehearsal.attr

    else:
        mock = rehearsal.func
        match_method = cst.Name("called_with")

    return cst.Call(
        func=cst.Attribute(
            value=cst.Call(
                func=decoy_method,
                args=[cst.Arg(value=mock), *_clean_args(kwargs)],
            ),
            attr=match_method,
        ),
        args=_clean_args(rehearsal.args),
    )


def _extract_conditional_starred_arg(
    value: cst.BaseExpression,
    decoy_func: cst.Attribute,
    kwargs: list[cst.Arg],
) -> cst.If:
    """Extract conditional from *(flag and [...] or [...])."""
    bool_op = cst.ensure_type(value, cst.BooleanOperation)
    left_bool_op = cst.ensure_type(bool_op.left, cst.BooleanOperation)

    condition = left_bool_op.left
    true_list = cst.ensure_type(left_bool_op.right, cst.List)
    false_list = cst.ensure_type(bool_op.right, cst.List)

    def _statements(
        elements: Sequence[cst.BaseElement],
    ) -> list[cst.SimpleStatementLine]:
        return [
            cst.SimpleStatementLine(
                body=[
                    cst.Expr(
                        _migrate_rehearsal_stmt(
                            decoy_func,
                            cst.ensure_type(element, cst.Element).value,
                            kwargs,
                        )
                    )
                ]
            )
            for element in elements
        ]

    else_body = _statements(false_list.elements)

    return cst.If(
        test=condition,
        body=cst.IndentedBlock(body=_statements(true_list.elements)),
        orelse=cst.Else(body=cst.IndentedBlock(body=else_body)) if else_body else None,
    )


def _migrate_rehearsal_stmt(
    decoy_method: cst.BaseExpression,
    rehearsal: cst.BaseExpression,
    kwargs: Sequence[cst.Arg],
) -> cst.Call:
    """Migrate a single rehearsal, handling both calls and bare attribute access."""
    if m.matches(rehearsal, m.Await()):
        rehearsal = cst.ensure_type(rehearsal, cst.Await).expression
    if m.matches(rehearsal, m.Attribute()):
        return cst.Call(
            func=cst.Attribute(
                value=cst.Call(
                    func=decoy_method,
                    args=[cst.Arg(value=rehearsal), *_clean_args(kwargs)],
                ),
                attr=cst.Name("get"),
            ),
            args=[],
        )
    return _migrate_rehearsal(
        decoy_method, cst.ensure_type(rehearsal, cst.Call), kwargs
    )


def _migrate_matcher(original: cst.Call) -> cst.Call:
    original_method = cst.ensure_type(original.func, cst.Attribute).attr.value
    original_args = original.args
    args: Sequence[cst.Arg | None] = original_args

    if original_method in ("AnythingOrNone", "Captor", "ValueCaptor"):
        renamed_method = "any"
    elif original_method == "Anything":
        renamed_method = "is_not"
        args = [cst.Arg(value=cst.Name("None"))]
    elif original_method == "IsA":
        renamed_method = "any"
        args = [
            _find_kwarg(original_args, "match_type", "type")
            or _rename_arg_at(
                original_args, 0, keyword="type", only_if_positional=True
            ),
            _find_kwarg(original_args, "attributes", "attrs")
            or _rename_arg_at(
                original_args, 1, keyword="attrs", only_if_positional=True
            ),
        ]
    elif original_method == "IsNot":
        renamed_method = "is_not"
    elif original_method == "HasAttributes":
        renamed_method = "any"
        args = [
            _rename_arg_at(original_args, 0, keyword="attrs", force_use_keyword=True)
        ]
    elif original_method in ("DictMatching", "ListMatching"):
        renamed_method = "contains"
    elif original_method == "StringMatching":
        renamed_method = "matches"
    elif original_method == "ErrorMatching":
        renamed_method = "error"
        args = [
            _find_kwarg(original_args, "error", "type")
            or _rename_arg_at(
                original_args, 0, keyword="type", only_if_positional=True
            ),
            _find_kwarg(original_args, "match", "match")
            or _rename_arg_at(
                original_args, 1, keyword="match", only_if_positional=True
            ),
        ]
    else:
        return original

    return cst.Call(
        func=cst.Attribute(value=cst.Name("Matcher"), attr=cst.Name(renamed_method)),
        args=_clean_args(args),
    )


def _rename_arg_at(
    original_args: Sequence[cst.Arg],
    index: int,
    keyword: str,
    force_use_keyword: bool = False,
    only_if_positional: bool = False,
) -> cst.Arg | None:
    if index >= len(original_args):
        return None

    original = original_args[index]

    if only_if_positional and original.keyword is not None:
        return None

    use_keyword = original.keyword is not None or force_use_keyword

    return cst.Arg(
        value=original.value,
        equal=(
            cst.AssignEqual(
                whitespace_before=cst.SimpleWhitespace(""),
                whitespace_after=cst.SimpleWhitespace(""),
            )
            if use_keyword
            else cst.MaybeSentinel.DEFAULT
        ),
        keyword=cst.Name(keyword) if use_keyword else None,
    )


def _find_kwarg(
    original_args: Sequence[cst.Arg],
    original_keyword: str,
    new_keyword: str,
) -> cst.Arg | None:
    """Find an arg by its original keyword name and rename it."""
    for arg in original_args:
        if arg.keyword is not None and arg.keyword.value == original_keyword:
            return cst.Arg(
                value=arg.value,
                keyword=cst.Name(new_keyword),
                equal=cst.AssignEqual(
                    whitespace_before=cst.SimpleWhitespace(""),
                    whitespace_after=cst.SimpleWhitespace(""),
                ),
            )
    return None


def _clean_args(args: Sequence[cst.Arg | None]) -> list[cst.Arg]:
    return [_clean_arg(arg) for arg in args if arg is not None]


def _clean_arg(arg: cst.Arg) -> cst.Arg:
    return arg.with_changes(
        comma=cst.MaybeSentinel.DEFAULT,
        whitespace_after_arg=cst.SimpleWhitespace(""),
    )
