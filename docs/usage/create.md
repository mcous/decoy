# Creating mocks

Decoy mocks are flexible objects that can be used in place of a class instance or a callable object, like a function. Mocks are created using the [decoy.Decoy.mock][] method.

## Mocking a class

To mock a class instance, pass the `cls` argument to `decoy.mock`. Decoy will inspect type annotations and method signatures to automatically configure a name for use in assertion messages and methods as synchronous or asynchronous. Decoy mocks are automatically deep.

```python
def test_my_thing(decoy: Decoy) -> None:
    some_dependency = decoy.mock(cls=SomeDependency)
```

To type checkers, the mock will appear to have the exact same type as the `cls` argument. The mock will also pass `isinstance` checks.

## Mocking a function

To mock a function, pass the `func` argument to `decoy.mock`. Decoy will inspect `func` to automatically configure a name for use in assertion messages and set the function as synchronous or asynchronous.

```python
def test_my_thing(decoy: Decoy) -> None:
    mock_function = decoy.mock(func=some_function)
```

To type checkers, the mock will appear to have the exact same type as the `func` argument. The function mock will pass `inspect.signature` checks.

## Creating a mock without a spec

You can call `decoy.mock` without using `cls` or `func`. A spec-less mock is useful for dependency interfaces like callback functions.

When creating a mock without a spec, you must use the `name` argument to give the mock a name to use in assertion messages. You must use the `is_async` argument if the created mock will be used as an asynchronous callable.

```python
def test_my_thing(decoy: Decoy) -> None:
    callback = decoy.mock(name="callback")
    async_callback = decoy.mock(name="async_callback", is_async=True)
```
