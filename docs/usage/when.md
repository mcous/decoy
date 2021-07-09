# Stubbing with when

A stub is a mock that is pre-configured to return a result or raise an error if called according to a specification. In Decoy, you use [decoy.Decoy.when][] to configure stubs.

## Using rehearsals to return a value

`Decoy.when` uses a "rehearsal" syntax to configure a stub's conditions:

```python
def test_my_thing(decoy: Decoy) -> None:
    database = decoy.create_decoy(spec=Database)
    subject = MyThing(database=database)

    decoy.when(database.get("some-id")).then_return(Model(id="some-id"))

    result = subject.get_model_by_id("some-id")

    assert result == Model(id="some-id")
```

The "rehearsal" is simply a call to the stub wrapped inside `decoy.when`. Decoy is able to differentiate between rehearsal calls and actual calls. If the mock is called later **in exactly the same way as a rehearsal**, it will behave as configured. If you need to loosen the "exact argument match" behavior, see [matchers](./matchers).

The "rehearsal" API gives us the following benefits:

-   Your test double will only return the value **if it is called correctly**
    -   Therefore, you avoid separate "configure return" and "assert called" steps
-   If you use type annotations, you get typechecking for free

## Raising an error

You can configure your stub to raise an error if called in a certain way:

```python
def test_my_thing_when_database_raises(decoy: Decoy) -> None:
    database = decoy.create_decoy(spec=Database)
    subject = MyThing(database=database)

    decoy.when(database.get("foo")).then_raise(KeyError(f"foo does not exist"))

    with pytest.raises(KeyError):
        subject.get_model_by_id("foo")
```

## Stubbing with async/await

If your dependency uses async/await, simply add `await` to the rehearsal:

```python
@pytest.mark.asyncio
async def test_my_async_thing(decoy: Decoy) -> None:
    database = decoy.create_decoy(spec=Database)
    subject = MyThing(database=database)

    decoy.when(await database.get("some-id")).then_return(Model(id="some-id"))

    result = await subject.get_model_by_id("some-id")

    assert result == Model(id="some-id")
```
