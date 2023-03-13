# Stubbing with when

A stub is an object that is configured to return a result or raise an error if called according to a specification. Use [decoy.Decoy.when][] to configure stubs.

## Configuring a stub

The `when` API uses a "rehearsal" syntax to configure a stub's conditions. To configure a stubbed behavior:

1. Form the expected call to the mock
2. Wrap it in `decoy.when`
3. Configure a behavior to trigger

```python
database = decoy.mock(name="database")

decoy.when(
    database.get("some-id")  # <-- rehearsal
).then_return(
    {"id": "some-id"}   # <-- behavior
)

assert database.get("some-id") == {"id": "some-id"}
```

Any time your dependency is called **in exactly the same way as the rehearsal**, the latest configured behavior that matches that rehearsal will be triggered. Otherwise, it will return the default value of `None`.

The "rehearsal" API gives us the following benefits:

-   Your test double will only take action **if it is called correctly**
    -   This avoids separate "configure return" and "assert called" steps
-   If you use type annotations, your rehearsal and behaviors can be type-checked
    -   This helps prevent configuring your stubs incorrectly

## Returning a value

To configure a return value, use [decoy.Stub.then_return][].

```python
database = decoy.mock(name="database")

decoy.when(
    database.get("some-id")  # <-- when `database.get` is called with "some-id"
).then_return(
    {"id": "some-id"}  # <-- then return the value `{"id": "some-id"}`
)

assert database.get("some-id") == {"id": "some-id"}
```

The value that you pass to `then_return` can be checked by your type-checker.

## Raising an error

To configure a raised exception when called, use [decoy.Stub.then_raise][]:

```python
database = decoy.mock(name="database")

decoy.when(
    database.get("foo")  # <-- when `database.get` is called with "foo"
).then_raise(
    KeyError("foo does not exist")  # <-- then raise a KeyError
)

subject.get_model_by_id("foo")  # will raise KeyError
```

!!! note

    Configuring a stub to raise will **make future rehearsals with the same arguments in the same test raise.** If you _must_ configure a new behavior after a raise in the same test, use a `try/except` block or `contextlib.suppress`. **You should probably never do this**, and instead use separate tests for different stub behaviors.

    ```python
    database = decoy.mock(name="database")

    decoy.when(database.get("foo")).then_raise(KeyError("oh no"))

    # ...later, in the same test

    def _database_get(key):
        with contextlib.suppress(KeyError):
            database.get(key)

    decoy.when(_database_get("foo")).then_return("hurray!")

    assert database.get("foo") == "hurray!"
    ```

## Performing an action

For complex situations, you may find that you want your stub to trigger a side-effect when called. For this, use [decoy.Stub.then_do][].

This is a powerful feature, and if you find yourself reaching for it, you should first consider if your code under test can be reorganized to be tested in a more straightforward manner.

```python
database = decoy.mock(name="database")

def _side_effect(key):
    print(f"hello {key}")
    return {"id": key}

decoy.when(
    database.get("foo")  # <-- when `database.get` is called with "foo"
).then_do(
    _side_effect  # <-- then run `_side_effect` and return its result
)

assert database.get("foo") == {id: "foo"}  # also prints "hello foo"
```

The action function passed to `then_do` will be passed any arguments given to the stub, and the stub will return whatever value is returned by the action.

## Loosening constraints with matchers

You may loosen rehearsal constraints using [decoy.matchers][]. See the [matchers usage guide](./matchers.md) for more information.

```python
say_hello = decoy.mock(name="say_hello")

decoy.when(
    say_hello(matchers.StringMatching("^foo")
).then_return(
    "hello"
)

assert say_hello("foo") == "hello"
assert say_hello("foobar") == "hello"
assert say_hello("fizzbuzz") is None
```

## Stubbing with async/await

If your mock uses async/await, simply add `await` to the rehearsal:

```python
compute_pi = decoy.mock(name="compute_pi", is_async=True)

decoy.when(
    await compute_pi()  # <-- when compute_pi() is awaited
).then_return(
    3  # <-- then return a value
)

assert await compute_pi() == 3
```

If you create a mock based on a class or function using `mock(cls=...)` or `mock(func=...)`, Decoy will configure functions as `async` according to the source object.

When using `then_do` with an `async` mock, the callback may also be `async`.

```python
compute_pi = decoy.mock(name="compute_pi", is_async=True)

async def _side_effect():
    print('close enough!')
    return 3

decoy.when(await compute_pi()).then_do(_side_effect)

assert await compute_pi() == 3  # also prints "close enough!"
```

## Only specify some arguments

If you don't care about some (or any) of the arguments passed to a stub, you can use the `ignore_extra_args` argument to tell Decoy to only check the arguments you pass.

```python
database = decoy.mock(cls=Database)

decoy.when(
    database.get("some-id"),
    ignore_extra_args=True,
).then_return(
    {"id": "some-id"}
)

# database.get called with more args than specified
result = database.get("some-id", hello="world")

# stubbed behavior still works
assert result == {"id": "some-id"}
```

!!! note

    The `ignore_extra_args` option is best used with functions that use default parameter values. If your rehearsal does use all required parameters as specified by a mock's source object, you will trigger a [decoy.warnings.IncorrectCallWarning][].
