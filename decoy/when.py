"""Create stubbings."""
from typing import TYPE_CHECKING, Callable, Generic

if TYPE_CHECKING:
    from . import Stub

from .core import StubCore, stub_store
from .spy import get_spy_core
from .spy_core import SpyCore
from .spy_events import SpyCall, WhenRehearsal
from .types import ParamsT, ReturnT


class When(Generic[ParamsT, ReturnT]):
    """Stub configuration API."""
    def __init__(self, spy_core: SpyCore, *, ignore_extra_args: bool) -> None:
        self._spy_core = spy_core
        self._ignore_extra_args = ignore_extra_args

    def called_with(self, *args: ParamsT.args, **kwargs: ParamsT.kwargs) -> 'Stub':
        """Configure a stubbing with the given arguments."""
        from . import Stub

        bound_args, bound_kwargs = self._spy_core.bind_args(*args, **kwargs)
        rehearsal = WhenRehearsal(
            spy=self._spy_core.info,
            payload=SpyCall(args=bound_args, kwargs=bound_kwargs, ignore_extra_args=self._ignore_extra_args),
        )
        stub_core = StubCore(rehearsal=rehearsal, stub_store=stub_store)

        return Stub(core=stub_core)


def when(mock: Callable[ParamsT, ReturnT], *, ignore_extra_args: bool = False) -> When[ParamsT, ReturnT]:
    """Configure a stubbing.

    Arguments:
        mock: The mock to configure.
        ignore_extra_args: Ignore any arguments not specified in te stubbing when matching.

    Returns:
        The stub configuration interface.
    """
    spy_core = get_spy_core(mock)
    return When(spy_core=spy_core, ignore_extra_args=ignore_extra_args)
