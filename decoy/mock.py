from typing import Any, Callable, Optional, overload

from .core import core
from .errors import MockNameRequiredError
from .types import ClassT, FuncT


@overload
def mock(*, cls: Callable[..., ClassT]) -> ClassT: ...

@overload
def mock(*, func: FuncT) -> FuncT: ...

@overload
def mock(*, name: str, is_async: bool = False) -> Any: ...

def mock(
    *,
    cls: Optional[Any] = None,
    func: Optional[Any] = None,
    name: Optional[str] = None,
    is_async: bool = False,
) -> Any:
    """Create a mock. See the [mock creation guide] for more details.

    [mock creation guide]: usage/create.md

    Arguments:
        cls: A class definition that the mock should imitate.
        func: A function definition the mock should imitate.
        name: A name to use for the mock. If you do not use
            `cls` or `func`, you should add a `name`.
        is_async: Force the returned spy to be asynchronous. This argument
            only applies if you don't use `cls` nor `func`.

    Returns:
        A spy typecast as the object it's imitating, if any.

    !!! example
        ```python
        def test_get_something(decoy: Decoy):
            db = decoy.mock(cls=Database)
            # ...
        ```
    """
    spec = cls or func

    if spec is None and name is None:
        raise MockNameRequiredError()

    return core.mock(spec=spec, name=name, is_async=is_async)
