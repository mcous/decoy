# Mock context managers

In Python, `with` statement [context managers][] provide an interface to execute code inside a given "runtime context." This context can define consistent, failsafe setup and teardown behavior. For example, Python's built-in file objects provide a context manager interface to ensure the underlying file resource is opened and closed cleanly, without the caller having to explicitly deal with it:

```python
with open("hello-world.txt", "r") as f:
    contents = f.read()
```

You can use Decoy to mock out your dependencies that provide a context manager interface.

[context managers]: https://docs.python.org/3/reference/datamodel.html#context-managers

## Generator-based context managers

Using the [contextlib][] module, you can [decorate a generator function][] or method to turn its yielded value into a context manager. To mock a generator function context manager, use [`Stub.then_enter_with`][decoy.next.Stub.then_enter_with].

```python
@contextlib.contextmanager
def open_config(path: str) -> collections.abc.Iterator[bool]:
    ...


def test_generator_context_manager(decoy: Decoy) -> None:
    mock_open_config = decoy.mock(func=open_config)

    decoy
        .when(mock_open_config)
        .called_with("some_flag")
        .then_enter_with(True)

    with mock_open_config("some_flag") as result:
        assert result is True
```

[contextlib]: https://docs.python.org/3/library/contextlib.html
[decorate a generator function]: https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager

## Class-based context managers

You can stub out a context manager's `__enter__` and `__exit__` method like any other method.

```python
def test_context_manager(decoy: Decoy) -> None:
    subject = decoy.mock(name="cm")

    decoy.when(subject.__enter__).called_with().then_return("hello world")

    with subject as result:
        assert result == "hello world"

    decoy.verify(subject.__exit__).called_with(None, None, None)
```

This also works with asynchronous `__aenter__` and `__aexit__`

## Context manager state

You can also configure stubs and verifications to only match calls made while a context manager mock is entered using the `is_entered` option to `called_with`.

| `is_entered` | Matching behavior                                           |
| ------------ | ----------------------------------------------------------- |
| `True`       | Only matches calls made between `__enter__` and `__exit__`  |
| `False`      | Only matches calls made if context manager is _not_ entered |
| `None`       | Match the call regardless of context manager entry state    |

```python
decoy
    .when(subject.read, is_entered=True)
    .called_with("some_flag")
    .then_return(True)

decoy
    .verify(subject.write, is_entered=True)
    .called_with("some_flag", "new_value")
```
