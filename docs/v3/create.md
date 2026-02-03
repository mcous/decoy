# Create a mock

Decoy mocks are flexible objects that can be used in place of a class instance or a callable object, like a function. Mocks are created using the [`Decoy.mock`][decoy.next.Decoy.mock] method.

## Default behaviors

Accessing any property of the mock will return a child mock, and calling the mock itself or any method of the mock will return `None`.

```python
my_mock = decoy.mock(name="my_mock")

assert my_mock() is None
assert my_mock.some_method("hello world") is None
assert my_mock.some_property.some_method("hey") is None
```

You can configure a mock's behaviors using [`decoy.when`](./when.md). You can make assertions about how a mock was called using [`decoy.verify`](./verify.md).

## Mock a class

To mock a class instance, pass the `cls` argument to `decoy.mock`. Decoy will inspect type annotations and method signatures to set a name for use in assertion messages, configure methods as synchronous or asynchronous, and understand function keyword arguments.

```python
some_dependency = decoy.mock(cls=SomeDependency)
```

To type checkers, the mock will appear to have the exact same type as the `cls` argument. The mock will also pass `isinstance` and `inspect.signature` checks.

## Mock a function

To mock a function, pass the `func` argument to `decoy.mock`. Decoy will inspect `func` to set a name for use in assertion messages, configure the mock as synchronous or asynchronous, and understand function keyword arguments.

```python
mock_function = decoy.mock(func=some_function)
```

To type checkers, the mock will appear to have the exact same type as the `func` argument. The function mock will pass `inspect.signature` checks.

## Creating a mock without a spec

You can call `decoy.mock` without using `cls` or `func`. A spec-free mock is useful for dependency interfaces like callback functions.

When creating a mock without a spec, you must use the `name` argument to give the mock a name to use in assertion messages. You must use the `is_async` argument if the created mock will be used as an asynchronous callable.

```python
callback = decoy.mock(name="callback")
async_callback = decoy.mock(name="async_callback", is_async=True)
```

## Mock an async function or method

If you pass Decoy a `cls` or `func` with asynchronous methods or functions, Decoy will automatically create asynchronous mocks. When creating mocks without `cls` or `func`, you can use the `is_async` option to create an asynchronous mock manually:

```python
async_mock = decoy.mock(name="async_mock", is_async=True)
```
