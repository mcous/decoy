# Migrate to v3

Recommended migration from v2:

1. Upgrade to `decoy>=2.4.0 <3`.
2. Incrementally migrate to the new API using `decoy.next`.
3. Once all tests are using the v3 syntax, upgrade to `v3` and swap `decoy.next` with `decoy`.

!!! warning

    `v3` is not yet released. This migration guide will change as `v3` is finalized.

## Setup

For an incremental migration, annotate a test's `decoy` fixture as `decoy.next.Decoy` to automatically opt-in that test to the preview API.

```diff
- from decoy import Decoy
+ from decoy.next import Decoy

  def test_when(decoy: Decoy) -> None:
      mock = decoy.mock(cls=SomeClass)
-     decoy.when(mock.foo("hello")).then_return("world")
+     decoy.when(mock.foo).called_with("hello").then_return("world")
```

## When

Replace the rehearsal syntax with [`When.called_with`][decoy.next.When.called_with]. See the [`when` guide][when-guide] for more details.

```diff
- decoy.when(mock("hello")).then_return("world")
+ decoy.when(mock).called_with("hello").then_return("world")
```

### Options

The `ignore_extra_args` option is still passed to [`Decoy.when`][decoy.next.Decoy.when], not `called_with`.

```diff
- decoy.when(mock("hello"), ignore_extra_args=True).then_return("world")
+ decoy.when(mock, ignore_extra_args=True).called_with("hello").then_return("world")
```

## Verify

Replace the rehearsal syntax with [`Verify.called_with`][decoy.next.Verify.called_with]. See the [`verify` guide][verify-guide] for more details.

```diff
- decoy.verify(mock("hello"))
+ decoy.verify(mock).called_with("hello")
```

### Options

The `times` and `ignore_extra_args` options are still passed to [`Decoy.verify`][decoy.next.Decoy.verify], not `called_with`.

```diff
- decoy.verify(mock("hello"), times=1)
+ decoy.verify(mock, times=1).called_with("hello")
```

### Verify call sequence

To verify a sequence of calls, call `Decoy.verify` from a [`Decoy.verify_order`][decoy.next.Decoy.verify_order] context.

```diff
- decoy.verify(
-     mock("a"),
-     mock("b"),
-     mock("c"),
- )
+ decoy.verify_order():
+   decoy.verify(mock).called_with("a")
+   decoy.verify(mock).called_with("b")
+   decoy.verify(mock).called_with("c")
```

## Async mocks

Using `called_with` in Decoy v3, it is no longer necessary to add `await` to `when` and `verify` calls for asynchronous mocks.

```diff
- decoy.when(await mock("hello")).then_return("world")
+ decoy.when(mock).called_with("hello").then_return("world")

- decoy.verify(await mock("hello"))
+ decoy.verify(mock).called_with("hello")
```

## Matchers

Matchers have been reworked to be more type-safe and easier to extend. See the [`Matcher` guide][matcher-guide] for more details.

```diff
- from decoy import Decoy, matchers
+ from decoy.next import Decoy, Matcher
```

| v2                        | v3                                                   |
| ------------------------- | ---------------------------------------------------- |
| `matchers.AnythingOrNone` | [`Matcher.any`][decoy.next.Matcher.any]              |
| `matchers.HasAttributes`  | [`Matcher.any(attrs=attrs)`][decoy.next.Matcher.any] |
| `matchers.IsA`            | [`Matcher.any(type=type)`][decoy.next.Matcher.any]   |
| `matchers.DictMatching`   | [`Matcher.contains`][decoy.next.Matcher.contains]    |
| `matchers.ListMatching`   | [`Matcher.contains`][decoy.next.Matcher.contains]    |
| `matchers.ErrorMatching`  | [`Matcher.error`][decoy.next.Matcher.error]          |
| `matchers.IsNot`          | [`Matcher.is_not`][decoy.next.Matcher.is_not]        |
| `matchers.Anything`       | [`Matcher.is_not(None)`][decoy.next.Matcher.is_not]  |
| `matchers.StringMatching` | [`Matcher.matches`][decoy.next.Matcher.matches]      |
| `matchers.ValueCaptor`    | Any other matcher; all matchers are now captors      |
| Custom matchers           | [`Matcher`][decoy.next.Matcher] + match function     |

## Attributes

The `decoy.prop` API has been replaced. See the [attributes guide][attributes-guide] for more details.

### When

Use [`When.get`][decoy.next.When.get], [`When.set`][decoy.next.When.set], and [`When.delete`][decoy.next.When.delete], to configure attribute stubs.

```diff
- decoy.when(mock.attr).then_return("world")
+ decoy.when(mock.attr).get().then_return("world")

- decoy.when(decoy.prop(mock.attr).set(42)).then_raise(RuntimeError("oh no"))
+ decoy.when(mock.attr).set(42).then_raise(RuntimeError("oh no"))

- decoy.when(decoy.prop(mock.attr).delete()).then_raise(RuntimeError("oh no"))
+ decoy.when(mock.attr).delete().then_raise(RuntimeError("oh no"))
```

### Verify

To verify attribute set and delete calls, use [`Verify.set`][decoy.next.Verify.set] and [`Verify.delete`][decoy.next.Verify.delete].

```diff
- decoy.verify(decoy.prop(mock.attr).set(42))
+ decoy.verify(mock.attr).set(42)

- decoy.verify(decoy.prop(mock.attr).delete())
+ decoy.verify(mock.attr).delete()
```

## Context managers

See the [context manager guide][context-manager-guide] for more details.

### `then_enter_with`

Mocking generator context managers has not changed aside from the `called_with` syntax.

```diff
- decoy.when(mock("hello")).then_enter_with("world")
+ decoy.when(mock).called_with("hello").then_enter_with("world")
```

### `__enter__` and `__exit__`

In v3, `__enter__` and `__exit__` can still be stubbed to test advanced context manager interactions. However, in v2, to configure a `ContextManager` mock to only behave a certain way when entered required jumping through hoops. In v3, both `when` and `verify` have an `is_entered` option to only match calls that happen inside the context.

`is_entered` is compatible with both `ContextManager`s and `AsyncContextManager`s.

```diff
  subject = decoy.mock(cls=MyCoolContextManager)

- def _handle_enter() -> None:
-     """Ensure `read` only works if context is entered."""
-     decoy.when(subject.read("some_flag")).then_return(True)
-
- def _handle_exit() -> None:
-     """Ensure test fails if subject calls `read` after exit."""
-     decoy.when(
-         subject.read("some_flag")
-     ).then_raise(AssertionError("Context manager was exited"))
-
- decoy.when(subject.__enter__()).then_do(_handle_enter)
- decoy.when(subject.__exit__(None, None, None)).then_do(_handle_exit)
+ decoy.when(subject.read, is_entered=True).called_with("some_flag").then_return(True)

  with subject:
      result = subject.get_config("some_flag")

  assert result is True
```

## Other breaking changes

- The `mypy` plugin is no longer needed and will be removed
- [`Decoy.mock`][decoy.next.Decoy.mock] is more strict about its arguments, and will raise [`MockSpecInvalidError`][decoy.errors.MockSpecInvalidError] if passed an invalid `spec` value.
- [`IncorrectCallWarning`][decoy.warnings.IncorrectCallWarning] has been upgraded to an error: [`SignatureMismatchError`][decoy.errors.SignatureMismatchError].
- Some "public" attributes have been removed from error classes.

[when-guide]: ./when.md
[verify-guide]: ./verify.md
[matcher-guide]: ./matchers.md
[attributes-guide]: ./attributes.md
[context-manager-guide]: ./context-managers.md
