# Decoy v3 Preview

The next major version of Decoy is a ground-up rebuild of the library. In the years since Decoy was first written, the Python typing system has advanced, especially when it comes to typing functions. These advancements, especially the addition of [`ParamSpec`][paramspec], unblocked a much simpler API (as well as internal implementation) for Decoy.

In order to ease the migration to the new API, the v3 API has been added as a preview to the v2 release (starting with `v2.4.0`) as `decoy.next`.

```diff
- from decoy import Decoy
+ from decoy.next import Decoy
```

!!! warning

    `decoy.next` is a **preview** and not subject to semver.
    No major changes are anticipated, but cannot be guaranteed until
    Decoy v3 is released.

## Setup

In order to use the v3 preview, you must be using:

- `decoy >= 2.4.0`
- `python >= 3.10`

Then, start trying out the new API!

```diff
- from decoy import Decoy
+ from decoy.next import Decoy


+ @pytest.fixture()
+ def decoy() -> collections.abc.Iterator[Decoy]:
+     """Create a Decoy v3 preview instance for testing."""
+     with Decoy.create() as decoy:
+         yield decoy


  def test_when(decoy: Decoy) -> None:
      mock = decoy.mock(cls=SomeClass)
-     decoy.when(mock.foo("hello")).then_return("world")
+     decoy.when(mock.foo).called_with("hello").then_return("world")


   def test_verify(decoy: Decoy) -> None:
      mock = decoy.mock(cls=SomeClass)
      mock.foo("hello")
-     decoy.verify(mock.foo("hello"))
+     decoy.verify(mock.foo).called_with("hello")
```

See the [migration guide](./migration.md) for more details.

[paramspec]: https://docs.python.org/3/library/typing.html#typing.ParamSpec
