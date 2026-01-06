# Contributing Guide

All contributions are greatly appreciated! Before contributing, please read the [code of conduct][].

## Development Setup

This project uses [uv][] to manage dependencies and builds. Once `uv` is installed, run `uv sync` to create a virtual environment and install development dependencies. Python >=3.10 is recommended for development.

```bash
git clone https://github.com/mcous/decoy.git
cd decoy
uv sync --python 3.12
```

## Development Tasks

This project uses [poethepoet][] to manage development tasks. Install it as a tool with `uv`:

```bash
uv tool install poethepoet
```

Once `poe` is installed, to quickly check everything, run the `all` task:

```bash
poe all
```

### Tests

Decoy's tests are run using [pytest][]. To run tests in watch mode:

```bash
poe test
```

To run tests once and report coverage

```bash
poe test-once
poe coverage
```

In an exciting twist, since version 1.6.0, Decoy's tests rely on Decoy itself to test (and more importantly, design) the relationships between Decoy's internal APIs. This means:

- Decoy's unit test suite serves as an end-to-end test of Decoy by virtue of existing (wow, very meta, actually kind of cool).
- Changes that break a small part of Decoy may result in a large number of test failures, because if Decoy breaks it can't be used to test itself.

If you find yourself in a situation where Decoy's test suite has blown up, **concentrate on getting the test suites that don't use Decoy to pass**. From there, lean on the type-checker to guide you to any components that aren't properly hooked up. Decoy also has a end-to-end smoke test suite (`tests/test_decoy.py`) that can be helpful in getting things back to green.

### Checks

Decoy's source code is typechecked with [mypy][] and linted/formatted with [ruff][].

```bash
poe check
poe lint
poe format
```

### Documentation

Decoy's documentation is built with [mkdocs][], which you can use to preview the documentation site locally.

```bash
<<<<<<< HEAD
poetry run poe docs
||||||| 1cebd3f
poetry run docs
=======
poe docs
>>>>>>> main
```

## Deploying

The library and documentation will be deployed to PyPI and GitHub Pages, respectively, by CI. We use [release please][] to automatically create release PRs based on [conventional commits][]. If bug fixes, features, or breaking changes have merged into `main`, there will be a release PR open. Merge the PR to release a new version.

[uv]: https://docs.astral.sh/uv/
[poethepoet]: https://github.com/nat-n/poethepoet
[code of conduct]: https://github.com/mcous/decoy/blob/main/CODE_OF_CONDUCT.md
[pytest]: https://docs.pytest.org/
[pytest-xdist]: https://github.com/pytest-dev/pytest-xdist
[mypy]: https://mypy.readthedocs.io
[ruff]: https://github.com/astral-sh/ruff
[mkdocs]: https://www.mkdocs.org/
[release please]: https://github.com/googleapis/release-please
[conventional commits]: https://www.conventionalcommits.org/
