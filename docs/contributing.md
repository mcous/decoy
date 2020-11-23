# Contributing Guide

## Development Setup

This project uses [poetry][] to manage dependencies and builds, and you will need to install it before working on Decoy.

Once poetry is installed, you should be good to set up a virtual environment and install development dependencies. While Decoy is supported on Python >= 3.7, Python >= 3.8 is recommended for development.

```bash
git clone https://github.com/mcous/decoy.git
cd decoy
poetry install
```

## Development Tasks

While working on the Decoy source code, the tasks will ensure code quality.

### Tests

Decoy's tests are run using [pytest][].

```bash
poetry run pytest
```

You can also run tests in watch mode using [pytest-watch][].

```bash
poetry run pytest-watch
```

### Checks

Decoy's source code is typechecked with [mypy][] and linted with [flake8][].

```bash
poetry run mypy
poetry run flake8
```

### Formatting

Decoy's source code is formatted using [black][].

```bash
poetry run black .
```

[poetry]: https://python-poetry.org/
[pytest]: https://docs.pytest.org/
[pytest-watch]: https://github.com/joeyespo/pytest-watch
[mypy]: https://mypy.readthedocs.io
[flake8]: https://flake8.pycqa.org
[black]: https://black.readthedocs.io
