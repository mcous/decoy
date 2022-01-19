"""Pytest plugin to setup and teardown a Decoy instance.

The plugin will be registered with pytest when you install Decoy. It adds a
fixture without modifying any other pytest behavior. Its usage is optional
but highly recommended.
"""
from typing import Iterable

import pytest

from decoy import Decoy


@pytest.fixture()
def decoy() -> Iterable[Decoy]:
    """Get a [decoy.Decoy][] container and [reset it][decoy.Decoy.reset] after the test.

    This function is function-scoped [pytest fixture][] that will be
    automatically inserted by the plugin.

    [pytest fixture]: https://docs.pytest.org/en/latest/how-to/fixtures.html

    Example:
        ```python
        def test_my_thing(decoy: Decoy) -> None:
            my_fake_func = decoy.mock()
            # ...
        ```
    """
    decoy = Decoy()
    yield decoy
    decoy.reset()
