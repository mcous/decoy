# Loosening assertions with matchers

Sometimes, when you're stubbing or verifying calls (or really when you're doing any sort of equality assertion in a test), you need to loosen a given assertion. For example, you may want to assert that a dependency is called with a string, but you don't care about the full contents of that string.

Decoy includes [decoy.matchers][], which has a set of Python classes with `__eq__` methods defined that you can use in rehearsals and/or assertions in place of actual values

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

When testing certain APIs, especially callback APIs, it can be helpful to capture the values of arguments passed to a given dependency. For this, Decoy provides [decoy.matchers.Captor][].

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

This is a pretty verbose way of writing a test, so in general, you may want to approach using `matchers.Captor` as a form of potential code smell / test pain. There are often better ways to structure your code for these sorts of interactions that don't involve private functions.

For further reading on when (or rather, when not) to use argument captors, check out [testdouble's documentation on its argument captor matcher](https://github.com/testdouble/testdouble.js/blob/main/docs/6-verifying-invocations.md#tdmatcherscaptor).
