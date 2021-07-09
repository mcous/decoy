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

### Tests

Decoy's tests are run using [pytest][].

```bash
poetry run pytest
```

You can also run tests in watch mode using [pytest-xdist][].

```bash
poetry run pytest --looponfail
```

In an exciting twist, since version 1.6.0, Decoy's tests rely on Decoy itself to test (and more importantly, design) the relationships between Decoy's internal APIs. This means:

-   Decoy's unit test suite serves as an end-to-end test of Decoy by virtue of existing (wow, very meta, actually kind of cool).
-   Changes that break a small part of Decoy may result in a large number of test failures, because if Decoy breaks it can't be used to test itself.

If you find yourself in a situation where Decoy's test suite has blown up, **concentrate on getting the test suites that don't use Decoy to pass**. From there, lean on the type-checker to guide you to any components that aren't properly hooked up. Decoy also has a end-to-end smoke test suite (`tests/test_decoy.py`) that can be helpful in getting things back to green.

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

### Documentation

Decoy's documentation is built with [mkdocs][], which you can use to preview the documentation site locally.

```bash
poetry run mkdocs serve
```

## Deploying

The library and documentation will be deployed to PyPI and GitHub Pages, respectively, by CI. To trigger the deploy, cut a new version and push it to GitHub.

Deploy adheres to [semantic versioning][], so care should be taken to bump accurately.

```bash
# checkout the main branch and pull down latest changes
git checkout main
git pull

# bump the version
# replace ${bump_version} with a bump specifier, like "minor"
poetry version ${bump_version}

# add the bumped pyproject.toml
git add pyproject.toml

# commit and tag the bump
# replace ${release_version} with the actual version string
git commit -m "chore(release): ${release_version}"
git tag -a v${release_version} -m "chore(release): ${release_version}"
git push --follow-tags
```

[poetry]: https://python-poetry.org/
[pytest]: https://docs.pytest.org/
[pytest-xdist]: https://github.com/pytest-dev/pytest-xdist
[mypy]: https://mypy.readthedocs.io
[flake8]: https://flake8.pycqa.org
[black]: https://black.readthedocs.io
[mkdocs]: https://www.mkdocs.org/
[semantic versioning]: https://semver.org/
