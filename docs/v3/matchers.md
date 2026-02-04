# Argument matchers

Sometimes, you may not care _exactly_ how a mock is called. For example, you may want to assert that a dependency is called with a string, but you don't care about the full contents of that string.

In Decoy, you can use a [`Matcher`][decoy.next.Matcher] in place of an actual argument value in [`when`][when-matcher-guide] and [`verify`][verify-matcher-guide] to "loosen" the match.

[when-matcher-guide]: ./when.md#loosen-constraints-with-matchers
[verify-matcher-guide]: ./verify.md#loosen-constraints-with-matchers

## Available matchers

| Matcher                                           | Description                                            |
| ------------------------------------------------- | ------------------------------------------------------ |
| [`Matcher`][decoy.next.Matcher]                   | Match based on a comparison function.                  |
| [`Matcher.any`][decoy.next.Matcher.any]           | Match any value, optionally by type and/or attributes. |
| [`Matcher.contains`][decoy.next.Matcher.contains] | Match a `list`, `dict`, or `str` based its contents.   |
| [`Matcher.error`][decoy.next.Matcher.error]       | Match an `Exception` based on its type and message.    |
| [`Matcher.is_not`][decoy.next.Matcher.is_not]     | Match anything that isn't a given value.               |
| [`Matcher.matches`][decoy.next.Matcher.matches]   | Match a string against a regular expression.           |

## Basic usage

Use the matcher instance wherever you would normally use a value. If you use static type checking, use [`Matcher.arg`][decoy.next.Matcher.arg], which type-casts the matcher as the expected type.

```python
from decoy.next import Decoy, Matcher

from .logger import Logger
from .my_thing import MyThing

def test_log_warning(decoy: Decoy):
    logger = decoy.mock(cls=Logger)
    subject = MyThing(logger=logger)

    subject.log_warning("Oh no, something went wrong with request abc123")

    decoy
        .verify(logger.warn)
        .called_with(Matcher.contains("abc123").arg)
```

A `Matcher` can also be used standalone, in an `assert`.

```python
assert "hello world" == Matcher.contains("hello")
```

### `Matcher.any`

Match any value, including `None`.

```python
any_matcher = Matcher.any()  # type: Matcher[Any]

assert "hello world" == any_matcher
assert 42 == any_matcher
assert None == any_matcher
```

You can scope down the matcher with an `isinstance` type. This will narrow `arg` and `value` to the passed type.

```python
str_matcher = Matcher.any(str)  # type: Matcher[str]

assert "hello world" == any_matcher
assert 42 != any_matcher
assert None != any_matcher
```

You can also scope the matcher to "anything with the given attributes."

```python
attrs_matcher = Matcher.any(attrs={"hello": "world"})  # type: Matcher[Any]
```

### `Matcher.contains`

Match mappings and sequences (including strings) that contain some values.

```python
assert {"hello": "world", "hola": "mundo"} == Matcher.contains({"hello": "world"})
assert ["hello", "world", "hola", "mundo"] == Matcher.contains(["hello", "world"])
assert "hello, world - hola, mundo" == Matcher.contains("hello, world")
```

When checking non-string sequences, you can specify that the values should appear in order.

```python
in_order_matcher = Matcher.contains(["hello", "world"], in_order=True)

assert ["hello", "world"] == in_order_matcher
assert ["world", "hello"] != in_order_matcher
```

### `Matcher.error`

### `Matcher.is_not`

Negate a match. For example, you may want to check that a value is simply anything except `None`.

```python
something_matcher = Matcher.is_not(None)  # type: Matcher[Any]

assert "hello world" == something_matcher
assert 42 == something_matcher
assert None != something_matcher
```

### `Matcher.matches`

Match a string against a regex pattern.

```python
hello_matcher = Matcher.matches("^hello")  # type: Matcher[str]

assert "hello world" == hello_matcher
assert "goodnight moon" != hello_matcher
```

## Capturing values

Sometimes, you need access to the actual values of arguments passed to a dependency. For this purpose, all matchers will capture any values that they are successfully compared with, available via [decoy.next.Matcher.value][] and [decoy.next.Matcher.values][].

For example, our test subject may register an event listener handler, and we want to test our subject's behavior when the event listener is triggered.

```python
from decoy.next import Decoy, Matcher

from .event_source import EventSource
from .event_consumer import EventConsumer


def test_event_listener(decoy: Decoy):
    event_source = decoy.mock(cls=EventSource)
    subject = EventConsumer(event_source=event_source)
    event_listener_matcher = Matcher(callable)

    # subject registers its listener when started
    subject.start_consuming()

    # verify listener attached and capture the listener
    decoy.verify(event_source.add_listener).called_with(event_listener_matcher.arg)

    # trigger the listener
    assert subject.has_heard_event is False
    event_listener_matcher.value()
    assert subject.has_heard_event is True
```

These "two stage" tests can become pretty verbose, so in general, approach using matcher-captured values as a form of potential code smell/test pain. There are often better ways to structure your code for these sorts of interactions that don't involve private functions. For further reading on when (or rather, when not) to use argument captors, check out [testdouble's documentation on its argument captor matcher](https://github.com/testdouble/testdouble.js/blob/main/docs/6-verifying-invocations.md#tdmatcherscaptor).

## Custom matchers

Use the base [`Matcher`][decoy.next.Matcher] class to create custom matchers. Pass `Matcher` a comparison function, and it will match any value that passes that function.

```python
def is_odd_int(target: object) -> bool:
    return isinstance(target, int) and target % 2 == 1

is_odd_matcher = Matcher(is_odd_int)  # type: Matcher[Any]

assert 1 == is_odd_matcher
assert 2 != is_odd_matcher
```

If you define your comparison function with [`TypeIs`](https://typing.python.org/en/latest/spec/narrowing.html#typeis), the `Matcher` will be narrowed to the appropriate type.

```python
def is_odd_int(target: object) -> TypeIs[int]:
    return isinstance(target, int) and target % 2 == 1

is_odd_matcher = Matcher(is_odd_int)  # type: Matcher[int]

assert_type(Matcher(is_odd_int), Matcher[int])
assert_type(is_odd_matcher.arg, int)
assert_type(is_odd_matcher.value, int)
```

This is especially useful with built-in inspection functions, like `callable`, which also return `TypeIs` guards.

```python
func_matcher = Matcher(callable)  # type: Matcher[Callable[..., object]]
```

### Custom matcher example

Custom matchers can be helpful when the value objects you are using as arguments are difficult to compare and out of your control. For example, Pandas [DataFrame][] objects do not return a `bool` from `__eq__`, which makes it difficult to compare calls. We can define a `data_frame_matcher` to work around this.

```python
import functools
import TypeIs from typing
import pandas as pd
from decoy import Matcher

def matchDataFrame(expected_data: object, target: object) -> TypeIs[pd.DataFrame]:
    return pd.DataFrame(expected_data).equals(target)

check_data = decoy.mock(name="check_data")
data_frame_matcher = Matcher(match=partial(matchDataFrame, {"x1": range(1, 42)}))

check_data(pd.DataFrame({"x1": range(1, 42)}))

decoy
    .verify(check_answer)
    .called_with(data_frame_matcher.arg)
```

[DataFrame]: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html
