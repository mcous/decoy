# Spy with `verify`

A spy is an object that simply records all calls made to it. Use [`Decoy.verify`][decoy.next.Decoy.verify] to make assertions about calls to a spy, after those calls have been made. Asserting that calls happened after the fact is useful for dependencies called solely for their side-effects.

!!! tip

    In general, units that solely produce side-effects are harder to test, typecheck, and maintain than units that return data. If a mocked dependency returns data that is used in your code, you should use [`when`][when-guide], not `verify`.

Usage of `when` and `verify` with the same mock are **mutually exclusive** within a test, and will trigger a warning. See the [`RedundantVerifyWarning`][redundantverifywarning-guide] guide for more information.

[when-guide]: ./when.md
[redundantverifywarning-guide]: ../usage/errors-and-warnings.md#redundantverifywarning

## Verify a call

The `verify` API is symmetrical with the [`when`][when-guide] API.

1. Access [`Decoy.verify`][decoy.next.Decoy.verify]
2. Assert on the call with [`Verify.called`][decoy.next.Verify.called], passing the mock and its expected arguments

```python
database = decoy.mock(name="database")

database.remove("some-id")  # <-- call to the spy

decoy.verify.called(database, "some-id")
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
decoy.verify(times=1).called(handler.should_be_called_once, "hello")

decoy.verify(times=2).called(handler.should_be_called_twice, "goodbye")

decoy.verify(times=0).called(handler.should_be_never_be_called, "fizzbuzz")
```

## Loosen constraints with matchers

You may loosen `called_with` constraints using [`Matchers`][decoy.next.Matcher]. See the [argument matchers guide](./matchers.md) for more information.

```python
say_hello = decoy.mock(name="say_hello")

say_hello("foobar")

decoy.verify.called(say_hello, Matcher.matches("^foo").arg)

with pytest.raises():
    decoy.verify.called(say_hello, Matcher.matches("^bar").arg)
```

## Verify order of multiple calls

If your code under test must call several dependencies in order, use [`Decoy.verify_order`][decoy.next.Decoy.verify_order]. Decoy will search through the list of all calls made to the given mocks and look for a matching ordered call sequence.

```python
with decoy.verify_order():
    decoy.verify.called(handler.first, "hello")
    decoy.verify.called(handler.second, "world")
```

## Only specify some arguments

If you don't care about some (or any) of the arguments passed to a spy, you can use the `ignore_extra_args` argument to tell Decoy to only check the arguments you pass.

```python
def log(message: str, meta: Optional[dict] = None) -> None:
    ...

mock_log = decoy.mock(func=log)

mock_log("hello world", meta={"foo": "bar"})

decoy.verify(ignore_extra_args=True).called(log, "hello world")
```

This can be combined with `times=0` to say "this dependency was never called," but your typechecker may complain about this:

```python
decoy.verify(times=0, ignore_extra_args=True).called(do_something)
```
