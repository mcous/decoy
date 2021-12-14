# Mocking context managers

In Python, `with` statement [context managers][] provide an extremely useful interface to execute code inside a given "runtime context." This context can define consistent, failsafe setup and teardown behavior. For example, Python's built-in file objects provide a context manager interface to ensure the underlying file resource is opened and closed cleanly, without the caller having to explicitly deal with it:

```python
with open("hello-world.txt", "r") as f:
    contents = f.read()
```

You can use Decoy to mock out your dependencies that should provide a context manager interface.

[context managers]: https://docs.python.org/3/reference/datamodel.html#context-managers

## Generator-based context managers

Using the [contextlib][] module, you can [decorate a generator function][] or method to turn its yielded value into a context manager. This is a great API, and one that Decoy is well-suited to mock. To mock a generator function context manager, use [decoy.Stub.then_enter_with][].

```python
import contextlib
from my_module.core import Core
from my_module.config import Config, ConfigLoader

def test_loads_config(decoy: Decoy) -> None:
    """It should load config from a ConfigLoader dependency.

    In this example, we know we're going to read/write config
    to/from an external source, like the filesystem. So we want to
    implement this dependency as a context manager to ensure
    resource cleanup.
    """
    config_loader = decoy.mock(ConfigLoader)
    config = decoy.mock(Config)

    subject = Core(config_loader=config_loader)

    decoy.when(config_loader.load()).then_enter_with(config)
    decoy.when(config.read("some_flag")).then_return(True)

    result = subject.get_config("some_flag")

    assert result is True
```

From this test, we could sketch out the following dependency APIs...

```python
# config.py
import contextlib
from typing import Iterator

class Config:
    def read(self, name: str) -> bool:
        ...

class ConfigLoader:
    @contextlib.contextmanager
    def load(self) -> Iterator[Config]:
        ...
```

...along with our test subject's implementation to pass the test...

```python
# core.py
from .config import Config, ConfigLoader

class Core:
    def __init__(self, config_laoder: ConfigLoader) -> None:
        self._config_loader = config_loader

    def get_config(self, name: str) -> bool:
        with self._config_loader.load() as config:
            return config.read(name)
```

[contextlib]: https://docs.python.org/3/library/contextlib.html
[decorate a generator function]: https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager

## General context managers

A context manager is simply an object with both `__enter__` and `__exit__` methods defined. Decoy mocks have both these methods defined, so they are compatible with the `with` statement. In the author's opinion, tests that mock `__enter__` and `__exit__` (or any double-underscore method) are harder to read and understand than tests that do not, so generator-based context managers should be prefered where applicable.

Using our earlier example, maybe you'd prefer to use a single `Config` dependency to both load the configuration resource and read values.

```python
import contextlib
from my_module.core import Core
from my_module.config import Config, ConfigLoader

def test_loads_config(decoy: Decoy) -> None:
    """It should load config from a Config dependency."""
    config = decoy.mock(Config)
    subject = Core(config=config)

    def _handle_enter() -> Config:
        """Ensure `read` only works if context is entered."""
        decoy.when(config.read("some_flag")).then_return(True)
        return config

    def _handle_exit() -> None:
        """Ensure test fails if subject calls `read` after exit."""
        decoy.when(
            config.read("some_flag")
        ).then_raise(AssertionError("Context manager was exitted"))

    decoy.when(config.__enter__()).then_do(_handle_enter)
    decoy.when(config.__exit__(None, None, None)).then_do(_handle_exit)

    result = subject.get_config("some_flag")

    assert result is True
```

From this test, our dependency APIs would be...

```python
# config.py
from __future__ import annotations
from types import TracebackType
from typing import Type, Optional

class Config:
    def __enter__(self) -> Config:
        ...

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        ...

    def read(self, name: str) -> bool:
        ...
```

...along with our test subject's implementation to pass the test...

```python
# core.py
from .config import Config

class Core:
    def __init__(self, config: Config) -> None:
        self._config = config

    def get_config(self, name: str) -> bool:
        with self._config as loaded_config:
            return loaded_config.read(name)
```

## Asynchronous context managers

Decoy is also compatible with mocking the async `__aenter__` and `__aexit__` methods of async context managers.

```python
import pytest
import contextlib
from my_module.core import Core
from my_module.config import Config, ConfigLoader

@pytest.mark.asyncio
async def test_loads_config(decoy: Decoy) -> None:
    """It should load config from a Config dependency."""
    config = decoy.mock(Config)
    subject = Core(config=config)

    async def _handle_enter() -> Config:
        """Ensure `read` only works if context is entered."""
        decoy.when(config.read("some_flag")).then_return(True)
        return config

    async def _handle_exit() -> None:
        """Ensure test fails if subject calls `read` after exit."""
        decoy.when(
            config.read("some_flag")
        ).then_raise(AssertionError("Context manager was exitted"))

    decoy.when(await config.__aenter__()).then_do(_handle_enter)
    decoy.when(await config.__aexit__()).then_do(_handle_exit)

    result = await subject.get_config("some_flag")

    assert result is True
```

This test spits out the following APIs and implementations...

```python
# config.py
from __future__ import annotations
from types import TracebackType
from typing import Type, Optional

class Config:
    async def __aenter__(self) -> Config:
        ...

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        ...

    def read(self, name: str) -> bool:
        ...
```

...along with our test subject's implementation to pass the test...

```python
# core.py
from .config import Config

class Core:
    def __init__(self, config: Config) -> None:
        self._config = config

    async def get_config(self, name: str) -> bool:
        async with self._config as loaded_config:
            return loaded_config.read(name)
```
