# Errors and warnings

Decoy's job as a mocking library is to provide you, the user, with useful design feedback about your code under test. Sometimes, this design feedback comes in the form of exceptions and warnings raised.

## Errors

### VerifyError

A [decoy.errors.VerifyError][] will be raised if a call to [decoy.Decoy.verify][] does not match the given rehearsal. This is a normal assertion, and means your code under test isn't behaving according to your test's specification.

```python
func = decoy.mock()

func("hello")

decoy.verify(func("goodbye"))  # raises a VerifyError
```

### MissingRehearsalError

A [decoy.errors.MissingRehearsalError][] will be raised if Decoy cannot pop a rehearsal call off its call stack during a call to [decoy.Decoy.when][] or [decoy.Decoy.verify][]. This is a runtime error and means **your test is using Decoy incorrectly**.

```python
decoy.when().then_return(42)  # raises a MissingRehearsalError
```

If you're working with async/await code, this can also happen if you forget to include `await` in your rehearsal, because the `await` is necessary for the spy's call handler to add the call to the stack.

```python
decoy.when(await some_async_func("hello")).then_return("world")  # all good
decoy.when(some_async_func("hello")).then_return("world")  # will raise
```

### MockNotAsyncError

A [decoy.errors.MockNotAsyncError][] will be raised if you pass an `async def` function to [decoy.Stub.then_do][] of a non-synchronous mock.

```python
async_mock = decoy.mock(name="async_mock", is_async=True)
async_mock = decoy.mock(name="sync_mock")

async def _handle_call(input: str) -> str:
    print(input)
    return "world"

decoy.when(await async_mock("hello")).then_do(_handle_call)  # all good
decoy.when(sync_mock("hello")).then_do(_handle_call)  # will raise
```

### MockNameRequiredError

A [decoy.errors.MockNameRequiredError][] will be raised if you call [decoy.Decoy.mock][] without `cls`, `func`, nor `name`.

If you pass `cls` or `func`, Decoy will infer the mock's name - to be used in assertion messages - from its source specification. If you don't pass a specification, you must give the mock an explicit name using the `name` argument.

```python
my_mock = decoy.mock(name="my_mock")
```

## Warnings

Decoy uses Python's [warnings system][] to provide feedback about dubious mock usage that isn't _technically_ incorrect. These warnings won't fail your tests, but you probably want to fix them.

### DecoyWarning

A [decoy.warnings.DecoyWarning][] is the base class of all warnings raised by Decoy. This warning will never be raised directly, but can be used in [warning filters][].

For example, you could set all Decoy warnings to errors or ignore them all entirely. Neither of these configurations are recommended; Decoy considers the default "warning" level to be correct.

```python
# ignore all Decoy warnings in a module (not recommended!)
pytestmark = pytest.mark.filterwarnings("ignore::decoy.warnings.DecoyWarning")
```

### MiscalledStubWarning

A [decoy.warnings.MiscalledStubWarning][] is a warning provided mostly for productivity convenience. If you configure a stub but your code under test calls the stub incorrectly, it can sometimes be difficult to immediately figure out what went wrong. This warning exists to alert you if:

-   A mock has at least 1 stubbing configured with [decoy.Decoy.when][]
-   A call was made to the mock that didn't match any configured stubbing

In the example below, our test subject is supposed to call a `DataGetter` dependency and pass the output data into a `DataHandler` dependency to get the result. However, in writing `Subject.get_and_handle_data`, we forgot to pass `data_id` into `DataGetter.get`.

```python
# test_subject.py

class Subject:
    def __init__(self, data_getter, data_handler):
        self._data_getter = data_getter
        self._data_handler = data_handler

    def get_and_handle_data(self, data_id):
        data = self._data_getter.get()  # <-- oops!
        result = self._data_handler.handle(data)
        return result

def test_subject(decoy: Decoy):
    data_getter = decoy.mock(cls=DataGetter)
    data_handler = decoy.mock(cls=DataHandler)
    subject = Subject(data_getter=data_getter, data_handler=data_handler)

    decoy.when(data_getter.get("data-id")).then_return(42)
    decoy.when(data_handler.handle(42)).then_return("good job")

    result = subject.get_and_handle_data("data-id")

    assert result == "good job"
```

When run, `self._data_getter.get()` will no-op and return `None`, because no matching stub configuration was found. That `None` will be fed into `self._data_handler.handle`, which will also no-op and return `None`, for the same reason. The test output will then tell us:

```shell
E       AssertionError: assert None == 'good job'
```

The test failed, which is good! But, the developer's next steps to fix the error aren't immediately obvious.

Your first reaction, especially if you're coming from a mocking library like [unittest.mock][], might be "We need to add an assertion that `data_getter.get` was called correctly." This would be bad, though! See [RedundantVerifyWarning](#RedundantVerifyWarning) below for why adding an assertion like this would be redundant and potentially harmful.

Even if we shouldn't add an assertion, we still want something to help us find the underlying issue. This is where `MiscalledStubWarning` comes in. When this test is run, Decoy will print the following warnings:

```shell
tests/test_example.py::test_subject
  /path/to/decoy/verifier.py:72: MiscalledStubWarning: Stub was called but no matching rehearsal found.
  Found 1 rehearsal:
  1.    DataGetter.get('data-id')
  Found 1 call:
  1.    DataGetter.get()
    warn(MiscalledStubWarning(calls=unmatched, rehearsals=rehearsals))

tests/test_example.py::test_subject
  /path/to/decoy/verifier.py:72: MiscalledStubWarning: Stub was called but no matching rehearsal found.
  Found 1 rehearsal:
  1.    DataHandler.handle(42)
  Found 1 call:
  1.    DataHandler.handle(None)
    warn(MiscalledStubWarning(calls=unmatched, rehearsals=rehearsals))
```

These warnings tell us that something probably went wrong with how the dependency was called, allowing us to fix the issue and move on.

### RedundantVerifyWarning

A [decoy.warnings.RedundantVerifyWarning][] is a warning provided to prevent you from writing redundant and over-constraining `verify` calls to mocks that have been configured with `when`.

Coming from [unittest.mock][], you're probably used to this workflow for mocks that return data:

1. Configure an unconditional return value or side effect
2. Call your test subject
3. Assert that mock was called correctly

Decoy, however, believes that, for data provider dependencies, asserting that a mock was called correctly is an over-constraint of the system. Instead, you set up Decoy stubs with:

1. Configure a return value or side effect **if and only if it is given the correct input**
2. Call your test subject
    - Your test subject will only trigger the configured behavior if it calls the mock correctly

This, however, may require a shift in how you think about mocks in your tests. Until that shift happens, you may be tempted to write:

```python
def test_subject(decoy: Decoy):
    data_getter = decoy.mock(cls=DataGetter)
    data_handler = decoy.mock(cls=DataHandler)
    subject = Subject(data_getter=data_getter, data_handler=data_handler)

    decoy.when(data_getter.get("data-id")).then_return(42)
    decoy.when(data_handler.handle(42)).then_return("good job")

    result = subject.get_and_handle_data("data-id")

    assert result == "good job"
    decoy.verify(data_getter.get("data-id"))  # redundant, but feels good
    decoy.verify(data_getter.handler(42))     # redundant, but feels good
```

Adding those `verify`s at the end may give you a feeling of "ok, good, now I'm completely testing the interaction," but that feeling is a fallacy. Thanks to the input specification in `when`, the test will already pass or fail correctly. At best, the `verify` calls do nothing, and at worst, they punish the test subject if it's able to accomplish its work in some other way, coupling our test to the subject's implementation unnecessarily.

If Decoy detects a `verify` with the same configuration of a `when`, it will raise a `RedundantVerifyWarning` to encourage you to remove the redundant, over-constraining `verify` call.

### IncorrectCallWarning

If you provide a Decoy mock with a specification `cls` or `func`, any calls to that mock will be checked according to `inspect.signature`. If the call does not match the signature, Decoy will raise a [decoy.warnings.IncorrectCallWarning][].

While Decoy will merely issue a warning, this call would likely cause the Python engine to error at runtime and should not be ignored.

```python
def some_func(val: string) -> int:
    ...

spy = decoy.mock(func=some_func)

spy("hello")                # ok
spy(val="world")            # ok
spy(wrong_name="ah!")       # triggers an IncorrectCallWarning
spy("too", "many", "args")  # triggers an IncorrectCallWarning
```

[warnings system]: https://docs.python.org/3/library/warnings.html
[warning filters]: https://docs.pytest.org/en/latest/how-to/capture-warnings.html
[unittest.mock]: https://docs.python.org/3/library/unittest.mock.html
