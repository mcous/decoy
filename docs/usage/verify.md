# Spying with verify

A spy is a mock that simply records all calls made to it. In Decoy, you use [decoy.Decoy.verify][] to make assertions about the calls to a spy.

If you're coming from `unittest.mock`, you're probably used to calling your code under test and _then_ verifying that your dependency was called correctly. Decoy can provide similar call verification.

## Caveats about using call verification

Asserting that calls happened after the fact can be useful, but **should only be used if the dependency is being called solely for its side-effect(s)**. Verification of interactions in this manner should be considered a last resort, because:

-   If you're calling a dependency to get data, then you can more precisely describe that relationship using [stubbing](./when)
-   Side-effects are harder to understand and maintain than pure functions, so in general you should try to side-effect sparingly

Stubbing and verification of a decoy are **mutually exclusive** within a test. If you find yourself wanting to both stub and verify the same dependency, then one or more of these is true:

-   The `verify` assertion is redundant
-   The dependency is doing too much based and should be refactored

## Using rehearsals to verify a call

The `verify` API uses the same "rehearsal" syntax as the [`when` API](./when).

```python
def test_my_thing(decoy: Decoy) -> None:
    database = decoy.mock(cls=Database)

    subject = MyThing(database=database)
    subject.delete_model_by_id("some-id")

    decoy.verify(database.remove("some-id"))
```

If Decoy is unable to find any calls matching the rehearsal inside `verify`, a [decoy.errors.VerifyError][] will be raised.

## Verifying with async/await

If your dependency uses async/await, simply add `await` to the rehearsal:

```python
@pytest.mark.asyncio
async def test_my_async_thing(decoy: Decoy) -> None:
    database = decoy.mock(cls=Database)

    subject = MyThing(database=database)
    await subject.delete_model_by_id("some-id")

    decoy.verify(await database.remove("some-id"))
```

## Verifying order of multiple calls

If your code under test must call several dependencies in order, you may pass multiple rehearsals to `verify`. Decoy will search through the list of all calls made to the given spies and look for the exact rehearsal sequence given, in order.

```python
decoy.verify(
    handler.call_first_procedure("hello"),
    handler.call_second_procedure("world"),
)
```

## Verifying a call count

You may want to verify that a call has been made a certain number of times, or verify that a call was never made. You can use the optional `times` argument to specify call count.

```python
decoy.verify(
    handler.should_be_called_twice(),
    times=2,
)

decoy.verify(
    handler.should_never_be_called(),
    times=0,
)
```

You may only use the `times` argument with single rehearsal.
