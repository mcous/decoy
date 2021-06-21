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
        <a href="https://mike.cousins.io/decoy/">https://mike.cousins.io/decoy/</a>
    </p>
</div>

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

## Setup

### Pytest

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

Decoy's rehearsal syntax can be a bit confusing to [mypy][] if a function is supposed to return `None`. Normally, [mypy will complain][] if you try to use a `None`-returning expression as a value, because this is almost always a mistake.

In Decoy, however, it's an intentional part of the API and _not_ a mistake. To suppress these errors, Decoy provides a mypy plugin that you should add to your configuration file:

```ini
# mypi.ini

# ...
plugins = decoy.mypy
# ...
```

[mypy]: https://mypy.readthedocs.io/
[mypy will complain]: https://mypy.readthedocs.io/en/stable/error_code_list.html#check-that-called-function-returns-a-value-func-returns-value

## Usage

### Stubbing

A stub is an object used in a test that is pre-configured to return a result or raise an error if called according to a specification. In Decoy, you specify a stub's call conditions with a "rehearsal", which is simply a call to the stub inside of a `decoy.when` wrapper.

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

### Verifying interactions

If you're coming from `unittest.mock`, you're probably used to calling your code under test and _then_ verifying that your dependency was called correctly. Decoy provides similar call verification using the same "rehearsal" mechanism that the stubbing API uses.

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

    # verify double called correctly with a rehearsal
    decoy.verify(logger.warn("oh no!"))
```

Asserting that calls happened after the fact can be useful, but **should only be used if the dependency is being called solely for its side-effect(s)**. Verification of interactions in this manner should be considered a last resort, because:

-   If you're calling a dependency to get data, then you can more precisely describe that relationship using [stubbing](#stubbing)
-   Side-effects are harder to understand and maintain than pure functions, so in general you should try to side-effect sparingly

Stubbing and verification of a decoy are **mutually exclusive** within a test. If you find yourself wanting to both stub and verify the same decoy, then one or more of these is true:

-   The assertions are redundant
-   The dependency is doing too much based on its input (e.g. side-effecting _and_ calculating complex data) and should be refactored

#### Verifying order of multiple calls

If your code under test must call several dependencies in order, you may pass multiple rehearsals to `verify`. Decoy will search through the list of all calls made to the given spies and look for the exact rehearsal sequence given, in order.

```python
decoy.verify(
    handler.call_first_procedure("hello"),
    handler.call_second_procedure("world"),
)
```

### Usage with async/await

Decoy supports async/await out of the box! Pass your async function or class with async methods to `spec` in `decoy.create_decoy_func` or `decoy.create_decoy`, respectively, and Decoy will figure out the rest.

When writing rehearsals on async functions and methods, remember to include the `await` with your rehearsal call:

```py
decoy.when(await mock_db.get_by_id("some-id")).then_return(mock_item)
```

### Matchers

Sometimes, when you're stubbing or verifying calls (or really when you're doing any sort of equality assertion in a test), you need to loosen a given assertion. For example, you may want to assert that a dependency is called with a string, but you don't care about the full contents of that string.

Decoy includes a set of matchers, which are simply Python classes with `__eq__` methods defined, that you can use in rehearsals and/or assertions.

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
        "Oh no, something went wrong with request ID abc123efg456",
        logger=logger
    )

    # verify double called correctly
    decoy.verify(
        logger.warn(matchers.StringMatching("request ID abc123efg456"))
    )
```

#### Capturing values with `matchers.captor`

When testing certain APIs, especially callback APIs, it can be helpful to capture the values of arguments passed to a given decoy.

For example, our test subject may register an anonymous event listener handler with a dependency, and we want to test our subject's behavior when the event listener is triggered.

```py
import pytest
from typing import cast, Optional
from decoy import Decoy, matchers

from .event_source import EventSource
from .event_consumer import EventConsumer


def test_event_listener(decoy: Decoy):
    event_source = decoy.create_decoy(spec=EventSource)
    subject = EventConsumer(event_source=event_source)
    captor = matchers.Captor()

    # subject registers its listener when started
    subject.start_consuming()

    # verify listener attached and capture the listener
    decoy.verify(event_source.register(event_listener=captor))

    # trigger the listener
    event_handler = captor.value  # or, equivalently, captor.values[0]

    assert subject.has_heard_event is False
    event_handler()
    assert subject.has_heard_event is True
```

This is a pretty verbose way of writing a test, so in general, you may want to approach using `matchers.captor` as a form of potential code smell / test pain. There are often better ways to structure your code for these sorts of interactions that don't involve anonymous / private functions.

For further reading on when (or rather, when not) to use argument captors, check out [testdouble's documentation on its argument captor matcher](https://github.com/testdouble/testdouble.js/blob/main/docs/6-verifying-invocations.md#tdmatcherscaptor).
