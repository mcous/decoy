"""Decoy mypy plugin."""
from typing import Callable, Optional, Type as ClassType

from mypy.errorcodes import FUNC_RETURNS_VALUE
from mypy.plugin import Plugin, MethodContext
from mypy.types import Type


class DecoyPlugin(Plugin):
    """A mypy plugin to remove otherwise valid errors from rehearsals."""

    def get_method_hook(
        self, fullname: str
    ) -> Optional[Callable[[MethodContext], Type]]:
        """Remove any func-returns-value errors inside `when` or `verify` calls."""
        if fullname in {"decoy.Decoy.verify", "decoy.Decoy.when"}:
            return self._handle_decoy_call

        return None

    def _handle_decoy_call(self, ctx: MethodContext) -> Type:
        errors_list = ctx.api.msg.errors.error_info_map.get(ctx.api.path, [])
        rehearsal_call_args = ctx.args[0] if len(ctx.args) > 0 else []
        error_removals = []

        for err in errors_list:
            if err.code == FUNC_RETURNS_VALUE:
                for arg in rehearsal_call_args:
                    if arg.line == err.line and arg.column == err.column:
                        error_removals.append(err)

        for err in error_removals:
            errors_list.remove(err)

        return ctx.default_return_type


def plugin(version: str) -> ClassType[DecoyPlugin]:
    """Get the DecoyPlugin class definition."""
    return DecoyPlugin
