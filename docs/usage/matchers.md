# Comparing with matchers

Sometimes, when you're stubbing or verifying calls (or really when you're doing any sort of equality assertion in a test), you need to loosen a given assertion. For example, you may want to assert that a dependency is called with a string, but you don't care about the full contents of that string.

Decoy includes the [decoy.matchers][] module, which is a set of Python classes with `__eq__` methods defined that you can use in rehearsals and/or assertions in place of actual values

## Available matchers

| Matcher                           | Description                                          |
| --------------------------------- | ---------------------------------------------------- |
| [decoy.matchers.Anything][]       | Matches any value that isn't `None`                  |
| [decoy.matchers.AnythingOrNone][] | Matches any value including `None`                   |
| [decoy.matchers.DictMatching][]   | Matches a `dict` based on some of its values         |
| [decoy.matchers.ListMatching][]   | Matches a `list` based on some of its values         |
| [decoy.matchers.ErrorMatching][]  | Matches an `Exception` based on its type and message |
| [decoy.matchers.HasAttributes][]  | Matches an object based on its attributes            |
| [decoy.matchers.IsA][]            | Matches using `isinstance`                           |
| [decoy.matchers.IsNot][]          | Matches anything that isn't a given value            |
| [decoy.matchers.StringMatching][] | Matches a string against a regular expression        |
| [decoy.matchers.ValueCaptor][]    | Captures the comparison value (see below)            |

## Basic usage

To use, import `decoy.matchers` and use a matcher wherever you would normally use a value.

```python
import pytest
from typing import cast, Optional
from decoy import Decoy, matchers

from .logger import Logger
from .my_thing import MyThing

def test_log_warning(decoy: Decoy):
    logger = decoy.mock(cls=Logger)

    subject = MyThing(logger=logger)

    # call code under test
    subject.log_warning("Oh no, something went wrong with request abc123efg456")

    # verify double called correctly
    decoy.verify(
        logger.warn(matchers.StringMatching("request abc123efg456"))
    )
```

## Capturing values

When testing certain APIs, especially callback APIs, it can be helpful to capture the values of arguments passed to a given dependency. For this, Decoy provides [decoy.matchers.ValueCaptor][].

For example, our test subject may register an event listener handler, and we want to test our subject's behavior when the event listener is triggered.

```py
import pytest
from typing import cast, Optional
from decoy import Decoy, matchers

from .event_source import EventSource
from .event_consumer import EventConsumer


def test_event_listener(decoy: Decoy):
    event_source = decoy.mock(cls=EventSource)
    subject = EventConsumer(event_source=event_source)
    captor = matchers.ValueCaptor()

    # subject registers its listener when started
    subject.start_consuming()

    # verify listener attached and capture the listener
    decoy.verify(event_source.register(event_listener=captor.matcher))

    # trigger the listener
    event_handler = captor.value  # or, equivalently, captor.values[0]

    assert subject.has_heard_event is False
    event_handler()
    assert subject.has_heard_event is True
```

This is a pretty verbose way of writing a test, so in general, approach using `matchers.ValueCaptor` as a form of potential code smell / test pain. There are often better ways to structure your code for these sorts of interactions that don't involve private functions.

For further reading on when (or rather, when not) to use argument captors, check out [testdouble's documentation on its argument captor matcher](https://github.com/testdouble/testdouble.js/blob/main/docs/6-verifying-invocations.md#tdmatcherscaptor).

## Writing custom matchers

You can write your own matcher class and use it wherever you would use a built-in matcher. All you need to do is define a class with an `__eq__` method:

```python
class Is42:
    def __eq__(self, other: object) -> bool:
        return other == 42

check_answer = decoy.mock(name="check_answer")

decoy.when(
    check_answer(Is42())
).then_return("huzzah!")

assert check_answer(42) == "huzzah!"
assert check_answer(43) is None
```

This is especially useful if the value objects you are using as arguments are difficult to compare and out of your control. For example, Pandas [DataFrame][] objects do not return a `bool` from `__eq__`, which makes it difficult to compare calls.

We can define a `MatchesDataFrame` class to work around this:

```python
import pandas as pd

class MatchesDataFrame:
    def __init__(self, data) -> None:
        self._data_frame = pd.DataFrame(data)

    def __eq__(self, other: object) -> bool:
        return self._data_frame.equals(other)

check_data = decoy.mock(name="check_data")

decoy.when(
    check_answer(MatchesDataFrame({"x1": range(1, 42)}))
).then_return("huzzah!")

assert check_data(pd.DataFrame({"x1": range(1, 42)})) == "huzzah!"
assert check_data(pd.DataFrame({"x1": range(1, 43)})) is None
```

[DataFrame]: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html
