"""Pytest plugin to setup and teardown a Decoy instance.

The plugin will be registered with pytest when you install Decoy. It adds a
fixture without modifying any other pytest behavior. Its usage is optional
but highly recommended.
"""

from typing import TYPE_CHECKING, Iterable, Union, get_type_hints

import pytest

from decoy import Decoy

if TYPE_CHECKING:
    from decoy.next import Decoy as DecoyNext


@pytest.fixture()
def decoy(
    request: pytest.FixtureRequest,
) -> "Iterable[Union[Decoy, DecoyNext]]":
    """Get a [decoy.Decoy][] container and [reset it][decoy.Decoy.reset] after the test.

    This function is function-scoped [pytest fixture][] that will be
    automatically inserted by the plugin.

    !!! tip

        This fixture will automatically opt-into the [v3 preview API][v3-preview]
        if annotated with `decoy.next.Decoy`.

    [pytest fixture]: https://docs.pytest.org/en/latest/how-to/fixtures.html
    [v3-preview]: ./v3/about.md

    !!! example
        ```python
        def test_my_thing(decoy: Decoy) -> None:
            my_fake_func = decoy.mock()
            # ...
        ```
    """
    try:
        decoy_hint = get_type_hints(request.function).get("decoy")
        is_next = decoy_hint.__module__.startswith("decoy.next")

    # purely defensive, probably won't ever raise
    except Exception:  # pragma: no cover
        is_next = False

    if is_next:
        from decoy.next import Decoy as DecoyNext

        with DecoyNext.create() as decoy_next:
            yield decoy_next
    else:
        decoy = Decoy()
        yield decoy
        decoy.reset()
