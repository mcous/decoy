# Decoy

[![ci badge][]][ci]
[![pypi version badge][]][pypi]
[![license badge][]][license]

[ci]: https://github.com/mcous/decoy/actions
[ci badge]: https://flat.badgen.net/github/checks/mcous/decoy/main
[pypi]: https://pypi.org/project/decoy/
[pypi version badge]: https://flat.badgen.net/pypi/v/decoy
[license]: https://github.com/mcous/decoy/blob/main/LICENSE
[license badge]: https://flat.badgen.net/github/license/mcous/decoy

> Opinionated, typed stubbing and verification library for Python

<https://mike.cousins.io/decoy/>

The Decoy library allows you to create, stub, and verify test double objects for your Python unit tests, so your tests are:

-   Less prone to insufficient tests due to unconditional stubbing
-   Covered by typechecking
-   Easier to fit into the Arrange-Act-Assert pattern

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

## Usage

### Setup

You'll want to create a test fixture to reset Decoy state between each test run. In [pytest][], you can do this by using a fixture to create a new Decoy instance for every test.

The examples below assume the following global test fixture:

```python
import pytest
from decoy import Decoy

@pytest.fixture
def decoy() -> Decoy:
    return Decoy()
```

Why is this important? The `Decoy` container tracks every fake that is created during a test so that you can define assertions using fully-typed rehearsals of your test double. It's important to wipe this slate clean for every test so you don't leak memory or have any state preservation between tests.

[pytest]: https://docs.pytest.org/

### Stubbing

A stub is a an object used in a test that is pre-configured to act in a certain way if called according to a spec, defined by a rehearsal. A "rehearsal" is simply a call to the stub inside of a `decoy.when` wrapper.

By pre-configuring the stub with specific rehearsals, you get the following benefits:

-   Your test double will only return your mock value **if it is called correctly**
-   You avoid separate "set up mock return value" and "assert mock called correctly" steps
-   If you annotate your test double with an actual type, the rehearsal will fail typechecking if called incorrectly

```python
import pytest
from typing import cast, Optional
from decoy import Decoy

from .database import Database, Model

def get_item(uid: str, db: Database) -> Optional[Model]:
  return db.get_by_id(uid)

def test_get_item(decoy: Decoy):
    mock_item = cast(Model, { "foo": "bar" })
    mock_db = decoy.create_decoy(spec=Database)

    # arrange stub using rehearsals
    decoy.when(mock_db.get_by_id("some-id")).then_return(mock_item)

    # call code under test
    some_result = get_item("some-id")
    other_result = get_item("other-id")

    # assert code result
    assert some_result == mock_item
    assert other_result is None
```

### Verification

If you're coming from `unittest.mock`, you're probably more used to calling your code under test and _then_ verifying that your test double was called correctly. Asserting on mock call signatures after the fact can be useful, but **should only be used if the dependency is being called solely for its side-effect(s)**.

Verification of decoy calls after they have occurred be considered a last resort, because:

-   If you're calling a method/function to get its data, then you can more precisely describe that relationship using [stubbing](#stubbing)
-   Side-effects are harder to understand and maintain than pure functions, so in general you should try to side-effect sparingly

Stubbing and verification of a decoy are **mutually exclusive** within a test. If you find yourself wanting to both stub and verify the same decoy, then one or more of these is true:

-   The assertions are redundant
-   The dependency is doing too much based on its input (e.g. side-effecting _and_ calculating complex data) and should be refactored

```python
import pytest
from typing import cast, Optional
from decoy import Decoy, verify

from .logger import Logger

def log_warning(msg: str, logger: Logger) -> None:
    logger.warn(msg)

def test_log_warning(decoy: Decoy):
    logger = decoy.create_decoy(spec=Logger)

    # call code under test
    some_result = log_warning("oh no!", logger)

    # verify double called correctly
    decoy.verify(logger.warn("oh no!"))
```

### Matchers

Sometimes, when you're stubbing or verifying decoy calls (or really when you're doing any sort of equality assertion in a test), you need to loosen a given assertion. For example, you may want to assert that a double is called with a string, but you don't care what the full contents of that string is.

Decoy includes a set of matchers, which are simply Python classes with `__eq__` methods defined, that you can use in decoy rehearsals and/or assertions.

```python
import pytest
from typing import cast, Optional
from decoy import Decoy, matchers

from .logger import Logger

def log_warning(msg: str, logger: Logger) -> None:
    logger.warn(msg)

def test_log_warning(decoy: Decoy):
    logger = decoy.create_decoy(spec=Logger)

    # call code under test
    some_result = log_warning(
        "Oh no, something horrible went wrong with request ID abc123efg456",
        logger=logger
    )

    # verify double called correctly
    decoy.verify(
        mock_logger.warn(matchers.StringMatching("something went wrong"))
    )
```
