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

You can also run tests in watch mode using [pytest-xdist][].

```bash
poetry run pytest --looponfail
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

### Documentation

Decoy's documentation is built with [mkdocs][], which you can use to preview the documentation site locally.

```bash
poetry run mkdocs serve
```

[poetry]: https://python-poetry.org/
[pytest]: https://docs.pytest.org/
[pytest-xdist]: https://github.com/pytest-dev/pytest-xdist
[mypy]: https://mypy.readthedocs.io
[flake8]: https://flake8.pycqa.org
[black]: https://black.readthedocs.io
[mkdocs]: https://www.mkdocs.org/

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

[semantic versioning]: https://semver.org/
