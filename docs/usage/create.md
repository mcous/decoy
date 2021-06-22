# Creating mocks

Decoy can create two kinds of mocks:

-   Mocks of a class instance
-   Mocks of a function

## Mocking a class

The [`create_decoy` method][decoy.Decoy.create_decoy] is used to create mock class instances. Decoy will inspect type annotations and method signatures to automatically configure methods as synchronous or asynchronous. Decoy mocks are automatically deep.

To typecheckers, the mock will appear to have the exact same type as the `spec` argument. The mock will also pass `isinstance` checks.

```python
def test_my_thing(decoy: Decoy) -> None:
    some_dependency = decoy.create_decoy(spec=SomeDependency)
```

## Mocking a function

The [`create_decoy_func` method][decoy.Decoy.create_decoy_func] is used to create a mock function instance. Decoy can inspect a `spec` function signature to automatically configure the function as syncronous or asynchronous. Otherwise, the `is_async` argument can force the mock to be asynchronous.

To typecheckers, the mock will appear to have the exact same type as the `spec` argument, if used.

```python
def test_my_thing(decoy: Decoy) -> None:
    mock_function = decoy.create_decoy_func(spec=some_function)
    free_async_function = decoy.create_decoy_func(is_async=True)
```
