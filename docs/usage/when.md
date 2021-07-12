# Stubbing with when

A stub is a mock that is pre-configured to return a result or raise an error if called according to a specification. In Decoy, you use [decoy.Decoy.when][] to configure stubs.

## Configuring a stub

`Decoy.when` uses a "rehearsal" syntax to configure a stub's conditions. To configure a stubbed behavior, form the expected call to the mock and wrap it in `when`:

```python
def test_my_thing(decoy: Decoy) -> None:
    database = decoy.mock(cls=Database)
    subject = MyThing(database=database)

    stub = decoy.when(
        database.get("some-id")  # <-- rehearsal
    )
    ...
```

Any time your dependency is called **in exactly the same way as the rehearsal**, whatever stub behaviors you configure will be triggered. If you need to loosen the "exact argument match" behavior, you can use [matchers](./matchers).

The "rehearsal" API gives us the following benefits:

-   Your test double will only take action **if it is called correctly**
    -   Therefore, you avoid separate "configure return" and "assert called" steps
-   If you use type annotations, you get typechecking for free

## Returning a value

To configure a return value, use [decoy.Stub.then_return][]:

```python
def test_my_thing(decoy: Decoy) -> None:
    database = decoy.mock(cls=Database)
    subject = MyThing(database=database)

    decoy.when(
        database.get("some-id")  # <-- when `database.get` is called with "some-id"
    ).then_return(
        Model(id="some-id")  # <-- then return the value `Model(id="some-id")`
    )

    result = subject.get_model_by_id("some-id")

    assert result == Model(id="some-id")
```

The value that you pass to `then_return` will be type-checked.

## Raising an error

To configure a raised exception when called, use [decoy.Stub.then_raise][]:

```python
def test_my_thing_when_database_raises(decoy: Decoy) -> None:
    database = decoy.mock(cls=Database)
    subject = MyThing(database=database)

    decoy.when(
        database.get("foo")  # <-- when `database.get` is called with "foo"
    ).then_raise(
        KeyError("foo does not exist")  # <-- then raise a KeyError
    )

    with pytest.raises(KeyError):
        subject.get_model_by_id("foo")
```

**Note:** configuring a stub to raise will **make future rehearsals with the same arguments raise.** If you must configure a new behavior after a raise, use a `try/except` block:

```python
decoy.when(database.get("foo")).then_raise(KeyError("oh no"))

# ...later

try:
    database.get("foo")
except Exception:
    pass
finally:
    # even though `database.get` is not inside the `when`, Decoy
    # will pop the last call off its stack to use as the rehearsal
    decoy.when().then_return("hurray!")
```

## Performing an action

For complex situations, you may find that you want your stub to trigger a side-effect when called. For this, use [decoy.Stub.then_do][].

This is a powerful feature, and if you find yourself reaching for it, you should first consider if your code under test can be reorganized to be tested in a more straightforward manner.

```python
def test_my_thing_when_database_raises(decoy: Decoy) -> None:
    database = decoy.mock(cls=Database)
    subject = MyThing(database=database)

    def _side_effect(key):
        print(f"Getting {key}")
        return Model(id=key)

    decoy.when(
        database.get("foo") # <-- when `database.get` is called with "foo"
    ).then_do(
        _side_effect # <-- then run `_side_effect`
    )

    with pytest.raises(KeyError):
        subject.get_model_by_id("foo")
```

The action function passed to `then_do` will be passed any arguments given to the stub, and the stub will return whatever value is returned by the action.

## Stubbing with async/await

If your dependency uses async/await, simply add `await` to the rehearsal:

```python
@pytest.mark.asyncio
async def test_my_async_thing(decoy: Decoy) -> None:
    database = decoy.mock(cls=Database)
    subject = MyThing(database=database)

    decoy.when(
        await database.get("some-id")  # <-- when database.get(...) is awaited
    ).then_return(
        Model(id="some-id")  # <-- then return a value
    )

    result = await subject.get_model_by_id("some-id")

    assert result == Model(id="some-id")
```
