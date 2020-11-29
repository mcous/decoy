"""Decoy mypy plugin."""
from mypy.plugin import Plugin


class DecoyPlugin(Plugin):
    def get_method_hook(self, fullname: str):
        if fullname.endswith("SyncFilesystem.write_json") or fullname.endswith("when"):
            print(fullname)
            return self._handle_context
        return None

    def _handle_context(self, context):
        print(context)
        print(context.context)
        print(context.api.scope.stack)
        return context.default_return_type


def plugin(version: str):
    # ignore version argument if the plugin works with all mypy versions.
    return DecoyPlugin
