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
poe docs
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
