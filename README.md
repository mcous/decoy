<div align="center">
    <h1>Decoy</h1>
    <img src="https://mike.cousins.io/decoy/img/decoy.png" width="256px">
    <p>Opinionated mocking library for Python</p>
    <p>
        <a title="CI Status" href="https://github.com/mcous/decoy/actions">
            <img src="https://flat.badgen.net/github/checks/mcous/decoy/main">
        </a>
        <a title="License" href="https://github.com/mcous/decoy/blob/main/LICENSE">
            <img src="https://flat.badgen.net/github/license/mcous/decoy">
        </a>
        <a title="PyPI Version"href="https://pypi.org/project/decoy/">
            <img src="https://flat.badgen.net/pypi/v/decoy">
        </a>
        <a title="Supported Python Versions" href="https://pypi.org/project/decoy/">
            <img src="https://flat.badgen.net/pypi/python/decoy">
        </a>
    </p>
    <p>
        <a href="https://mike.cousins.io/decoy/">Usage guide and documentation</a>
    </p>
</div>

The Decoy library allows you to create, stub, and verify fully-typed, async/await-friendly mocks in your Python unit tests, so your tests are:

-   Less prone to insufficient tests due to unconditional stubbing
-   Easier to fit into the Arrange-Act-Assert pattern
-   Covered by typechecking

The Decoy API is heavily inspired by / stolen from the excellent [testdouble.js][] and [Mockito][] projects.

## Install

```bash
# pip
pip install decoy

# poetry
poetry add --dev decoy
```

## Setup

### Pytest setup

Decoy ships with its own [pytest][] plugin, so once Decoy is installed, you're ready to start using it via its pytest fixture, called `decoy`.

```python
# test_my_thing.py
from decoy import Decoy

def test_my_thing_works(decoy: Decoy) -> None:
    # ...
```

The `decoy` fixture is function-scoped and will ensure that all stub and spy state is reset between every test.

### Mypy Setup

Decoy's API can be a bit confusing to [mypy][]. To suppress mypy errors that may be emitted during valid usage of the Decoy API, we have a mypy plugin that you should add to your configuration file:

```ini
# mypy.ini

# ...
plugins = decoy.mypy
# ...
```

## Basic Usage

This example assumes you are using [pytest][]. See Decoy's [documentation][] for a more detailed usage guide and API reference.

### Define your test

Decoy will add a `decoy` fixture that provides its mock creation API.

```python
from decoy import Decoy
from todo import TodoAPI, TodoItem
from todo.store TodoStore

def test_add_todo(decoy: Decoy) -> None:
    ...
```

### Create a mock

Use `decoy.mock` to create a mock based on some specification. From there, inject the mock into your test subject.

```python
def test_add_todo(decoy: Decoy) -> None:
    todo_store = decoy.mock(cls=TodoStore)
    subject = TodoAPI(store=todo_store)
    ...
```

See [creating mocks][] for more details.

### Stub a behavior

Use `decoy.when` to configure your mock's behaviors. For example, you can set the mock to return a certain value when called in a certain way using `then_return`:

```python
def test_add_todo(decoy: Decoy) -> None:
    """Adding a todo should create a TodoItem in the TodoStore."""
    todo_store = decoy.mock(cls=TodoStore)
    subject = TodoAPI(store=todo_store)

    decoy.when(
        todo_store.add(name="Write a test for adding a todo")
    ).then_return(
        TodoItem(id="abc123", name="Write a test for adding a todo")
    )

    result = subject.add("Write a test for adding a todo")
    assert result == TodoItem(id="abc123", name="Write a test for adding a todo")
```

See [stubbing with when][] for more details.

### Verify a call

Use `decoy.verify` to assert that a mock was called in a certain way. This is best used with dependencies that are being used for their side-effects and don't return a useful value.

```python
def test_remove_todo(decoy: Decoy) -> None:
    """Removing a todo should remove the item from the TodoStore."""
    todo_store = decoy.mock(cls=TodoStore)
    subject = TodoAPI(store=todo_store)

    subject.remove("abc123")

    decoy.verify(todo_store.remove(id="abc123"))
```

See [spying with verify][] for more details.

[testdouble.js]: https://github.com/testdouble/testdouble.js
[mockito]: https://site.mockito.org/
[pytest]: https://docs.pytest.org/
[mypy]: https://mypy.readthedocs.io/
[documentation]: https://mike.cousins.io/decoy/
[creating mocks]: https://mike.cousins.io/decoy/usage/create/
[stubbing with when]: https://mike.cousins.io/decoy/usage/when/
[spying with verify]: https://mike.cousins.io/decoy/usage/verify/
