# Stub with `when`

A stub is an object that is configured to return a value or raise an error if called according to a specification. Use [`Decoy.when`][decoy.next.Decoy.when] to configure stubs.

Decoy stubs are **conditional**, unlike [`unittest.MagicMock.return_value`][MagicMock.return_value], which is unconditional. By using a conditional stub, you ensure your mock will only take action **if it is called correctly**, avoiding the separate `return_value` and `assert_called_with` steps needed with `MagicMock`.

[MagicMock.return_value]: https://docs.python.org/3/library/unittest.mock.html#unittest.mock.Mock.return_value

## Configure a stub

1. Pass the mock to [`Decoy.when`][decoy.next.Decoy.when]
2. Pass the expected arguments to [`When.called_with`][decoy.next.When.called_with]
3. Configure a behavior, e.g. [`Stub.then_return`][decoy.next.Stub.then_return]

```python
database = decoy.mock(name="database")

decoy
    .when(database.get)
    .called_with("some-id")
    .then_return({"id": "some-id"})

assert database.get("some-id") == {"id": "some-id"}
```

Any time your dependency is called with exactly the same arguments as a configured stubbing, the latest matching behavior will be triggered. Otherwise, it will return the default value of `None`. The arguments passed to `called_with` are statically type-checked against the spec. If multiple stubbings match a call, the latest configured stubbing will be used.

The behavior of `when` may be customized with the following options.

| Option              | Type   | Description                                           |
| ------------------- | ------ | ----------------------------------------------------- |
| `times`             | `int`  | Only perform the configured action a number of times. |
| `ignore_extra_args` | `bool` | See [only specify some arguments][ignore-extra-args]. |
| `is_entered`        | `bool` | See [context manager state][is-entered].              |

[ignore-extra-args]: #only-specify-some-arguments
[is-entered]: ./context-managers.md#context-manager-state

## Return a value

To configure a return value, use [`Stub.then_return`][decoy.next.Stub.then_return].

```python
database = decoy.mock(name="database")

decoy
    .when(database.get)
    .called_with("some-id")
    .then_return({"id": "some-id"})

assert database.get("some-id") == {"id": "some-id"}
```

The value that you pass to `then_return` is statically type-checked against the spec.

## Raise an error

To configure a raised exception when called, use [`Stub.then_raise`][decoy.next.Stub.then_raise]:

```python
database = decoy.mock(name="database")

decoy
    .when(database.get)
    .called_with("foo")
    .then_raise(KeyError("foo does not exist"))

with pytest.raises(KeyError):
    subject.get_model_by_id("foo")
```

## Perform an action

For complex situations, you may find that you want your stub to trigger a function when called. For this, use [`Stub.then_do`][decoy.next.Stub.then_do]. The action function you pass to `then_do` will be passed any arguments given to the stub, and the stub will return whatever value is returned by the action.

If you find yourself reaching for this method often, this may be a sign your code could be reorganized to be tested in a more straightforward manner.

!!! tip

    When using an asynchronous mock, the function you pass to `then_do` may be either synchronous or asynchronous. However, if you pass an asynchronous function to `then_do` for a synchronous mock, you will trigger a [`MockNotAsyncError`](../usage/errors-and-warnings.md#mocknotasyncerror).

```python
database = decoy.mock(name="database")

def _side_effect(key):
    print(f"hello {key}")
    return {"id": key}

decoy
    .when(database.get)
    .called_with("foo")
    .then_do(_side_effect)

assert database.get("foo") == {id: "foo"}  # also prints "hello foo"
```

## Loosen constraints with matchers

You may loosen `called_with` constraints using [`Matcher`][decoy.next.Matcher]. See the [argument matchers guide](./matchers.md) for more information.

```python
say_hello = decoy.mock(name="say_hello")

decoy
    .when(say_hello)
    .called_with(Matcher.matches("^foo").arg)
    .then_return("hello")

assert say_hello("foo") == "hello"
assert say_hello("foobar") == "hello"
assert say_hello("fizzbuzz") is None
```

## Stub a sequence of behaviors

All `Stub` methods accept multiple behavior values. If you pass multiple behaviors, the mock will perform each one in sequence as it is called.

```python
decoy
    .when(mock)
    .called_with("hello")
    .then_return("world", "mundo", "verden")

assert mock("hello") == "world"
assert mock("hello") == "mundo"
assert mock("hello") == "verden"
```

## Only specify some arguments

If you don't care about some arguments passed to a stub, you can use the `ignore_extra_args` argument to only compare against the arguments you pass.

!!! tip

    The `ignore_extra_args` option is best used with functions with optional parameters, otherwise your type-checker will probably complain.

```python
database = decoy.mock(cls=Database)

decoy
    .when(database.get, ignore_extra_args=True)
    .called_with("some-id")
    .then_return({"id": "some-id"})

# database.get called with more args than specified
result = database.get("some-id", hello="world")

# stubbed behavior still works
assert result == {"id": "some-id"}
```
