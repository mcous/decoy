<div align="center">
    <h1>Decoy</h1>
    <img src="https://mike.cousins.io/decoy/img/decoy.png" width="256px">
    <p>Opinionated, typed stubbing and verification library for Python</p>
    <p>
        <a href="https://github.com/mcous/decoy/actions">
            <img title="CI Status" src="https://flat.badgen.net/github/checks/mcous/decoy/main">
        </a>
        <a href="https://pypi.org/project/decoy/">
            <img title="PyPI Version" src="https://flat.badgen.net/pypi/v/decoy">
        </a>
        <a href="https://github.com/mcous/decoy/blob/main/LICENSE">
            <img title="License" src="https://flat.badgen.net/github/license/mcous/decoy">
        </a>
    </p>
    <p>
        <a href="https://mike.cousins.io/decoy/">Usage guide and documentation</a>
    </p>
</div>

The Decoy library allows you to create, stub, and verify fully-typed, async/await friendly mocks in your Python unit tests, so your tests are:

-   Less prone to insufficient tests due to unconditional stubbing
-   Easier to fit into the Arrange-Act-Assert pattern
-   Covered by typechecking

The Decoy API is heavily inspired by / stolen from the excellent [testdouble.js][] and [Mockito][] projects.

[testdouble.js]: https://github.com/testdouble/testdouble.js
[mockito]: https://site.mockito.org/

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

[pytest]: https://docs.pytest.org/

### Mypy Setup

Decoy's API can be a bit confusing to [mypy][]. To suppress mypy errors that may be emitted during valid usage of the Decoy API, we have a mypy plugin that you should add to your configuration file:

```ini
# mypi.ini

# ...
plugins = decoy.mypy
# ...
```

[mypy]: https://mypy.readthedocs.io/
