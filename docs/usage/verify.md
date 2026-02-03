# Spying with verify

A spy is an object that simply records all calls made to it. Use [decoy.Decoy.verify][] to make assertions about calls to a spy, after those calls have been made. Asserting that calls happened after the fact is useful for dependencies called solely for their side-effects.

In general, functions that produce side-effects instead of returning data are harder to test, typecheck, and maintain. To use Decoy to minimize side effects and increase the maintainability of your code, prefer writing tests - and therefore, your dependencies' APIs - to use stubbing with [when][] rather than call verification with `verify`.

!!! tip

    If a mocked dependency returns data that is used by your test subject, you should use [when][], not `verify`. Prefer using `when` over `verify` to guide the structure of your code to minimize side-effects.

Usage of `when` and `verify` with the same mock are **mutually exclusive** within a test, and will trigger a warning. See the [RedundantVerifyWarning][] guide for more information.

[when]: ./when.md
[redundantverifywarning]: ./errors-and-warnings.md#redundantverifywarning

## Verifying a call

The `verify` API uses the same "rehearsal" syntax as [when][].

1. Form the expected call to the mock
2. Wrap it in `decoy.verify`

```python
database = decoy.mock(name="database")

database.remove("some-id")  # <-- call to the spy

decoy.verify(
    database.remove("some-id"),  # <-- verify the spy was called in this manner
    times=1,
)
```

By default, if Decoy finds _any_ call matching the `verify` invocation, the call will pass. However, if a matching call is not found, a [VerifyError][] will be raised.

[verifyerror]: ./errors-and-warnings.md#verifyerror

## Verifying a call count

You can use the optional `times` argument to specify call count. With `times`, the call to `verify` will fail if there is the incorrect number of matching calls.

!!! tip

    Prefer using the `times` argument, and only omit it if it _really_ doesn't matter how many times a dependency is called by the test subject.

```python
decoy.verify(
    handler.should_be_called_once(),
    times=1,
)

decoy.verify(
    handler.should_be_called_twice(),
    times=2,
)

decoy.verify(
    handler.should_never_be_called(),
    times=0,
)
```

## Loosening constraints with matchers

You may loosen rehearsal constraints using [decoy.matchers][]. See the [matchers usage guide](./matchers.md) for more information.

```python
say_hello = decoy.mock(name="say_hello")

say_hello("foobar")

decoy.verify(say_hello(matchers.StringMatching("^foo")), times=1)  # passes
decoy.verify(say_hello(matchers.StringMatching("^bar")), times=1)  # raises
```

## Verifying with async/await

If your dependency uses async/await, simply add `await` to the rehearsal:

```python
cow_say = decoy.mock(name="cow_say", is_async=True)

await cow_say("moo")

decoy.verify(
    await cow_say("moo"),
    times=1,
)
```

If you create a mock based on a class or function using `mock(cls=...)` or `mock(func=...)`, Decoy will configure functions as `async` according to the source object.

## Verifying order of multiple calls

If your code under test must call several dependencies in order, you may pass multiple rehearsals to `verify`. Decoy will search through the list of all calls made to the given spies and look for the exact rehearsal sequence given, in order.

```python
decoy.verify(
    handler.call_first_procedure("hello"),
    handler.call_second_procedure("world"),
)
```

## Only specify some arguments

If you don't care about some (or any) of the arguments passed to a spy, you can use the `ignore_extra_args` argument to tell Decoy to only check the arguments you pass.

```python
def log(message: str, meta: Optional[dict] = None) -> None:
    ...

# ...
log("hello world", meta={"foo": "bar"})
# ...

decoy.verify(
    log("hello world"),
    ignore_extra_args=True,
)
```

This can be combined with `times=0` to say "this dependency was never called," but your typechecker may complain about this:

```python
# verify that something was never called in any way
decoy.verify(do_something(), times=0, ignore_extra_args=True)
```
