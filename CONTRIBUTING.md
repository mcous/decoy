# Contributing Guide

All contributions are greatly appreciated! Before contributing, please read the [code of conduct][].

## Development Setup

This project uses [Poetry][] to manage dependencies and builds, and you will need to install it before working on Decoy.

Once Poetry is installed, you should be good to set up a virtual environment and install development dependencies. Python >=3.10 is recommended for development.

```bash
git clone https://github.com/mcous/decoy.git
cd decoy
poetry install
```

## Development Tasks

Decoy uses [poethepoet][] to manage development tasks. If you want to quickly check everything, run the following:

```shell
poetry run poe all
```

[poethepoet]: https://github.com/nat-n/poethepoet

### Tests

Decoy's tests are run using [pytest][]. To run tests in watch mode:

```bash
poetry run poe test
```

To run tests once and report coverage

```bash
poetry run poe test-once
poetry run poe coverage
```

In an exciting twist, since version 1.6.0, Decoy's tests rely on Decoy itself to test (and more importantly, design) the relationships between Decoy's internal APIs. This means:

-   Decoy's unit test suite serves as an end-to-end test of Decoy by virtue of existing (wow, very meta, actually kind of cool).
-   Changes that break a small part of Decoy may result in a large number of test failures, because if Decoy breaks it can't be used to test itself.

If you find yourself in a situation where Decoy's test suite has blown up, **concentrate on getting the test suites that don't use Decoy to pass**. From there, lean on the type-checker to guide you to any components that aren't properly hooked up. Decoy also has a end-to-end smoke test suite (`tests/test_decoy.py`) that can be helpful in getting things back to green.

### Checks

Decoy's source code is typechecked with [mypy][] and linted/formatted with [ruff][].

```bash
poetry run poe check
poetry run poe lint
poetry run poe format
```

### Documentation

Decoy's documentation is built with [mkdocs][], which you can use to preview the documentation site locally.

```bash
poetry run poe docs
```

## Deploying

The library and documentation will be deployed to PyPI and GitHub Pages, respectively, by CI. To trigger the deploy, cut a new version and push it to GitHub.

Decoy adheres to [semantic versioning][], so care should be taken to bump accurately.

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

[code of conduct]: https://github.com/mcous/decoy/blob/main/CODE_OF_CONDUCT.md
[poetry]: https://python-poetry.org/
[pytest]: https://docs.pytest.org/
[pytest-xdist]: https://github.com/pytest-dev/pytest-xdist
[mypy]: https://mypy.readthedocs.io
[ruff]: https://github.com/astral-sh/ruff
[mkdocs]: https://www.mkdocs.org/
[semantic versioning]: https://semver.org/
