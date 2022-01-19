<div align="center">
    <img alt="Decoy logo" src="https://mike.cousins.io/decoy/img/decoy.png" width="256px">
    <h1 class="decoy-title">Decoy</h1>
    <p>Opinionated mocking library for Python</p>
    <p>
        <a title="CI Status" href="https://github.com/mcous/decoy/actions">
        <img src="https://img.shields.io/github/workflow/status/mcous/decoy/Continuous%20integration/main?style=flat-square"></a>
        <a title="Code Coverage" href="https://app.codecov.io/gh/mcous/decoy/"><img src="https://img.shields.io/codecov/c/github/mcous/decoy?style=flat-square"></a>
        <a title="License" href="https://github.com/mcous/decoy/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mcous/decoy?style=flat-square"></a>
        <a title="PyPI Version"href="https://pypi.org/project/decoy/"><img src="https://img.shields.io/pypi/v/decoy?style=flat-square"></a>
        <a title="Supported Python Versions" href="https://pypi.org/project/decoy/"><img src="https://img.shields.io/pypi/pyversions/decoy?style=flat-square"></a>
    </p>
    <p>
        <a href="https://mike.cousins.io/decoy/" class="decoy-hidden">Usage guide and documentation</a>
    </p>
</div>

Decoy is a mocking library designed for **effective and productive test-driven development** in Python. If you want to use tests to guide the structure of your code, Decoy might be for you!

Decoy mocks are **async/await** and **type-checking** friendly. Decoy is heavily inspired by (and/or stolen from) the excellent [testdouble.js][] and [Mockito][] projects. The Decoy API is powerful, easy to read, and strives to help you make good decisions about your code.

## Install

```bash
# pip
pip install decoy

# poetry
poetry add --dev decoy

# pipenv
pipenv install --dev decoy
```

## Setup

### Pytest setup

Decoy ships with its own [pytest][] plugin, so once Decoy is installed, you're ready to start using it via its pytest fixture, called `decoy`.

```python
# test_my_thing.py
from decoy import Decoy

def test_my_thing_works(decoy: Decoy) -> None:
    ...
```

### Mypy setup

By default, Decoy is compatible with Python [typing][] and type-checkers like [mypy][]. However, stubbing functions that return `None` can trigger a [type checking error](https://mypy.readthedocs.io/en/stable/error_code_list.html#check-that-called-function-returns-a-value-func-returns-value) during correct usage of the Decoy API. To suppress these errors, add Decoy's plugin to your mypy configuration.

```ini
# mypy.ini
plugins = decoy.mypy
```

### Other testing libraries

Decoy works well with [pytest][], but if you use another testing library or framework, you can still use Decoy! You just need to do two things:

1. Create a new instance of [`Decoy()`](https://mike.cousins.io/decoy/api/#decoy.Decoy) before each test
2. Call [`decoy.reset()`](https://mike.cousins.io/decoy/api/#decoy.Decoy.reset) after each test

For example, using the built-in [unittest][] framework, you would use the `setUp` fixture method to do `self.decoy = Decoy()` and the `tearDown` method to call `self.decoy.reset()`. For a working example, see [`tests/test_unittest.py`](https://github.com/mcous/decoy/blob/main/tests/test_unittest.py).

## Basic Usage

This basic example assumes you are using [pytest][]. For more detailed documentation, see Decoy's [usage guide][] and [API reference][].

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
[unittest]: https://docs.python.org/3/library/unittest.html
[typing]: https://docs.python.org/3/library/typing.html
[mypy]: https://mypy.readthedocs.io/
[api reference]: https://mike.cousins.io/decoy/api/
[usage guide]: https://mike.cousins.io/decoy/usage/create/
[creating mocks]: https://mike.cousins.io/decoy/usage/create/
[stubbing with when]: https://mike.cousins.io/decoy/usage/when/
[spying with verify]: https://mike.cousins.io/decoy/usage/verify/
