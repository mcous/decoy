# Spy with `verify`

A spy is an object that simply records all calls made to it. Use [`Decoy.verify`][decoy.next.Decoy.verify] to make assertions about calls to a spy, after those calls have been made. Asserting that calls happened after the fact is useful for dependencies called solely for their side-effects.

!!! tip

    In general, units that solely produce side-effects are harder to test, typecheck, and maintain than units that return data. If a mocked dependency returns data that is used in your code, you should use [`when`][when-guide], not `verify`.

Usage of `when` and `verify` with the same mock are **mutually exclusive** within a test, and will trigger a warning. See the [`RedundantVerifyWarning`][redundantverifywarning-guide] guide for more information.

[when-guide]: ./when.md
[redundantverifywarning-guide]: ../usage/errors-and-warnings.md#redundantverifywarning

## Verify a call

The `verify` API is symmetrical with the [`when`][when-guide] API.

1. Pass the mock to [`Decoy.verify`][decoy.next.Decoy.verify]
2. Assert on the arguments with [`Verify.called_with`][decoy.next.Verify.called_with]

```python
database = decoy.mock(name="database")

database.remove("some-id")  # <-- call to the spy

decoy
  .verify(database)
  .called_with("some-id")
```

By default, if Decoy finds _any_ call matching the `verify` invocation, the call will pass. However, if a matching call is not found, a [`VerifyError`][verifyerror-guide] will be raised.

The behavior of `verify` may be customized with the following options.

| Option              | Type   | Description                                           |
| ------------------- | ------ | ----------------------------------------------------- |
| `times`             | `int`  | Check for an exact number of calls.                   |
| `ignore_extra_args` | `bool` | See [only specify some arguments][ignore-extra-args]. |
| `is_entered`        | `bool` | See [context manager state][is-entered].              |

[ignore-extra-args]: #only-specify-some-arguments
[is-entered]: ./context-managers.md#context-manager-state
[verifyerror-guide]: ../usage/errors-and-warnings.md#verifyerror

## Verify a call count

You can use the optional `times` argument to specify call count. With `times`, the call to `verify` will fail if there is the incorrect number of matching calls.

```python
decoy
    .verify(handler.should_be_called_once, times=1)
    .called_with("hello")

decoy
    .verify(handler.should_be_called_twice, times=2)
    .called_with("goodbye")

decoy
    .verify(handler.should_be_never_be_called, times=0)
    .called_with("fizzbuzz")
```

## Loosen constraints with matchers

You may loosen rehearsal constraints using [`matchers`][decoy.matchers]. See the [matchers usage guide](../usage/matchers.md) for more information.

```python
say_hello = decoy.mock(name="say_hello")

say_hello("foobar")

decoy.verify(say_hello).called_with(matchers.StringMatching("^foo"))

with pytest.raises():
    decoy.verify(say_hello).called_with(matchers.StringMatching("^bar"))
```

## Verify order of multiple calls

If your code under test must call several dependencies in order, use [`Decoy.verify_order`][decoy.next.Decoy.verify_order]. Decoy will search through the list of all calls made to the given spies and look for a matching ordered call sequence.

```python
with decoy.verify_order():
    decoy.verify(handler.first).called_with("hello")
    decoy.verify(handler.second).called_with("world")
```

## Only specify some arguments

If you don't care about some (or any) of the arguments passed to a spy, you can use the `ignore_extra_args` argument to tell Decoy to only check the arguments you pass.

```python
def log(message: str, meta: Optional[dict] = None) -> None:
    ...

mock_log = decoy.mock(func=log)

mock_log("hello world", meta={"foo": "bar"})

decoy.verify(log, ignore_extra_args=True).called_with("hello world")
```

This can be combined with `times=0` to say "this dependency was never called," but your typechecker may complain about this:

```python
decoy.verify(do_something, times=0, ignore_extra_args=True).called_with()
```
