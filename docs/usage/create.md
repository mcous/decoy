# Creating mocks

Decoy can create two kinds of mocks:

-   Mocks of a class instance
-   Mocks of a function

Mocks are created using the [decoy.Decoy.mock][] method.

## Mocking a class

To mock a class instance, pass the `cls` argument to `decoy.mock`. Decoy will inspect type annotations and method signatures to automatically configure methods as synchronous or asynchronous. Decoy mocks are automatically deep.

```python
def test_my_thing(decoy: Decoy) -> None:
    some_dependency = decoy.mock(cls=SomeDependency)
```

To type checkers, the mock will appear to have the exact same type as the `cls` argument. The mock will also pass `isinstance` checks.

## Mocking a function

To mock a function, pass the `func` argument to `decoy.mock`. Decoy will inspect `func` to automatically configure the function as synchronous or asynchronous.

```python
def test_my_thing(decoy: Decoy) -> None:
    mock_function = decoy.mock(func=some_function)
```

To type checkers, the mock will appear to have the exact same type as the `func` argument. The function mock will pass `inspect.signature` checks.

## Creating an anonymous mock

If you use neither `cls` nor `func` when calling `decoy.mock`, you will get an anonymous mock. You can use the `is_async` argument to return an asynchronous mock.

```python
def test_my_thing(decoy: Decoy) -> None:
    anon_function = decoy.mock()
    async_anon_function = decoy.mock(is_async=True)
```
