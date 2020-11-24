# Why Use Decoy?

The Python testing world already has [unittest.mock][] for creating fakes, so why is a library like Decoy even necessary?

The `MagicMock` class (and friends) provided by the Python standard library are great, which is why Decoy uses them under the hood. They are, however:

-   Not very opinionated in how they are used
-   Not able to adhere to type annotations of your actual interfaces

At its core, Decoy wraps `MagicMock` with a more opinionated, strictly typed interface to encourage well written tests and, ultimately, well written source code.

[unittest.mock]: https://docs.python.org/3/library/unittest.mock.html

## Recommended Reading

Decoy is heavily influenced by and/or stolen from the [testdouble.js][] and [Mockito][] projects. These projects have both been around for a while (especially Mockito), and their docs are valuable resources for learning how to test and mock effectively.

If you have the time, you should check out:

-   Mockito Wiki - [How to write good tests](https://github.com/mockito/mockito/wiki/How-to-write-good-tests)
-   Test Double Wiki - [Discovery Testing](https://github.com/testdouble/contributing-tests/wiki/Discovery-Testing)
-   Test Double Wiki - [Test Double](https://github.com/testdouble/contributing-tests/wiki/Test-Double)

[testdouble.js]: https://github.com/testdouble/testdouble.js
[mockito]: https://site.mockito.org/

## Creating and Using a Stub

A [stub][] is a specific type of test fake that:

-   Can be configured to respond in a certain way if given certain inputs
-   Will no-op if given output outside of its pre-configured specifications

Stubs are great for simulating dependencies that provide data to or run calculations on input data for the code under test.

For the following examples, let's assume:

-   We're testing a library to deal with `Book` objects
-   That library depends on a `Database` provider to store objects in a database
-   That library depends on a `Logger` interface to log access

[stub]: https://en.wikipedia.org/wiki/Test_stub

### Stubbing with a MagicMock

```python
# setup
from pytest
from unittest.mock import MagicMock
from typing import cast

from my_lib.database import Database
from my_lib.bookshelf import get_book, Book


@pytest.fixture
def mock_database() -> MagicMock:
    return MagicMock(spec=Database)

@pytest.fixture
def mock_book() -> Book:
    return cast(Book, {"title": "The Metamorphosis"})
```

`MagicMock` does not provide an explicit stubbing interface, so to stub you could:

```python
# option 1:
#   - return mock data unconditionally
#   - assert dependency was called correctly after the fact

def test_get_book(mock_database: MagicMock, mock_book: Book) -> None:
    # arrange mock to always return mock data
    mock_database.get_by_id.return_value = mock_book

    # exercise the code under test
    result = get_book("unique-id", database=mock_database)

    # assert that the result is correct
    assert result == mock_book
    # also assert that the database mock was called correctly
    mock_database.get_by_id.assert_called_with("unique-id)
```

```python
# option 2: create a side-effect function to check the conditions
def test_get_book(mock_database: MagicMock, mock_book: Book) -> None:
    def stub_get_by_id(uid: str) -> Optional[Book]:
        if uid == "unique-id":
            return mock_book
        else:
            return None

    # arrange mock to always return mock data
    mock_database.get_by_id.side_effect = stub_get_by_id

    # exercise the code under test
    result = get_book("unique-id", database=mock_database)

    # assert that the result is correct
    # because of the `if` in the side-effect, we know the stub was called
    # correctly because there's no other way the code-under-test could have
    # gotten the mock_book data
    assert result == mock_book
```

Both of these options have roughly the same upside and downsides:

-   Upside: `MagicMock` is part of the Python standard library
-   Downside: they're both a little difficult to read
    -   Option 1 separates the input checking from output value, and they appear in reverse chronological order (you define the dependency output before you define the input)
    -   Option 2 forces you to create a whole new function and assign it to the `side_effect` value
-   Downside: `MagicMock` is effectively `Any` typed
    -   `return_value` and `assert_called_with` are not typed according to the dependency's type definition
    -   A manual `side_effect`, if typed, needs to be manually typed, which may not match the actual dependency type definition

Option 1 has another downside, specifically:

-   The mocked return value is unconditional
    -   If the assert step is wrong or accidentally skipped, the code-under-test is still fed the mock data
    -   This increases the likelihood of a false pass or insufficient test coverage

### Stubbing with Decoy

```python
# setup
from pytest
from decoy import Decoy

from my_lib.database import Database
from my_lib.bookshelf import get_book, Book

@pytest.fixture
def decoy() -> Decoy:
    return Decoy()

@pytest.fixture
def mock_database(decoy: Decoy) -> Database:
    return decoy.create_decoy(spec=Database)

@pytest.fixture
def mock_book() -> Book:
    return cast(Book, {"title": "The Metamorphosis"})
```

Decoy wraps `MagicMock` with a simple, rehearsal-based stubbing interface.

```python
def test_get_book(decoy: Decoy, mock_database: Database, mock_book: Book) -> None:
    # arrange stub to return mock data when called correctly
    decoy.when(
        # this is a rehearsal, which might look a little funny at first
        # it's an actual call to the test double that Decoy captures
        mock_database.get_by_id("unique-id")
    ).then_return(mock_book)

    # exercise the code under test
    result = get_book("unique-id", database=mock_database)

    # assert that the result is correct
    assert result == mock_book
```

Benefits to note over the vanilla `MagicMock` versions:

-   The rehearsal syntax for stub configuration is terse but very easy to read
    -   Inputs and outputs from the dependency are specified together
    -   You specify the inputs _before_ outputs, which can be easier to grok
-   The entire test fits neatly into "arrange", "act", and "assert" phases
-   Decoy casts test doubles as the actual types they are mimicking
    -   This means stub configuration arguments _and_ return values are type-checked

## Creating and Using a Spy

A [spy][] is another kind of test fake that simply records calls made to it. Spies are useful to model dependencies that are used for their side-effects rather than providing or calculating data.

[spy]: https://github.com/testdouble/contributing-tests/wiki/Spy

### Spying with a MagicMock

```python
# setup
from pytest
from decoy import Decoy

from my_lib.logger import Logger
from my_lib.bookshelf import get_book, Book


@pytest.fixture
def decoy() -> Decoy:
    return Decoy()


@pytest.fixture
def mock_logger() -> MagicMock:
    return MagicMock(spec=Logger)
```

`MagicMock` is well suited to spying, since it's an object that records all calls made to it.

```python
def test_get_book_logs(mock_logger: MagicMock) -> None:
    # exercise the code under test
    get_book("unique-id", logger=mock_logger)

    # assert logger spy was called correctly
    mock_logger.log.assert_called_with(level="debug", msg="Get book unique-id")
```

The only real downside to `MagicMock` in this case is the lack of typechecking.

### Spying with Decoy

```python
# setup
from pytest
from decoy import Decoy

from my_lib.logger import Logger
from my_lib.bookshelf import get_book, Book


@pytest.fixture
def decoy() -> Decoy:
    return Decoy()


@pytest.fixture
def mock_logger(decoy: Decoy) -> Logger:
    return decoy.create_decoy(spec=Logger)
```

For verification of spies, Decoy doesn't do much except set out to add typechecking.

```python
def test_get_book_logs(decoy: Decoy, mock_logger: Logger) -> None:
    # exercise the code under test
    get_book("unique-id", logger=mock_logger)

    # assert logger spy was called correctly
    # uses the same type-checked "rehearsal" syntax as stubbing
    decoy.verify(
        mock_logger(level="debug", msg="Get book unique-id")
    )
```
