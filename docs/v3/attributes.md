# Mock attributes

Python [property attributes][] provide an interface for creating read-only properties and properties with getters, setters, and deleters. You can use Decoy to stub these properties.

[property attributes]: https://docs.python.org/3/library/functions.html#property

## Default behavior

Unlike mock method calls - which have a default return value of `None` - Decoy's default return value for attribute access is **another mock**. You don't need to configure anything explicitly if you need a `@property` getter to return another mock; Decoy will inspect type annotations and configure the proper child mock for you.

```python
class Child:
    ...

class Parent:
    @property
    def child(self) -> Child:
        ...

mock_parent = decoy.mock(cls=Parent)

assert isinstance(mock_parent, Dependency)
assert isinstance(mock_parent.child, Child)
```

You may also manually set any mock attribute to "opt out" of Decoy for a given attribute. To opt back into Decoy, delete the attribute.

```python
dep = decoy.mock(cls=Parent)

dep.child = "don't worry about it"
assert dep.child == "don't worry about it"

del dep.child
assert isinstance(mock_parent.child, Child)
```

## Stub attribute access

### Stub a getter

Use [`When.get`][decoy.next.When.get] stub a return value for an attribute instead of returning a child mock.

```python
dependency = decoy.mock(name="dependency")

decoy.when(dependency.some_property).get().then_return(42)

assert dep.some_property == 42
```

You can also configure any other behavior, like raising an error.

```python
dependency = decoy.mock(name="dependency")

decoy
    .when(dependency.some_property)
    .get()
    .then_raise(RuntimeError("oh no"))

with pytest.raises(RuntimeError, match="oh no"):
    dependency.some_property
```

### Stub a setter or deleter

While you cannot stub a return value for a getter or setter, because set and delete expressions do not return a value in Python, you _can_ stub a `raise` or a side effect with [`When.set`][decoy.next.When.set] and [`When.delete`][decoy.next.When.delete].

```python
dependency = decoy.mock(name="dependency")

decoy
    .when(dependency.some_property)
    .set(42)
    .then_raise(RuntimeError("oh no"))

decoy
    .when(dependency.some_property)
    .delete()
    .then_raise(RuntimeError("what a disaster"))

with pytest.raises(RuntimeError, match="oh no"):
    dependency.some_property = 42

with pytest.raises(RuntimeError, match="what a disaster"):
    del dependency.some_property
```

## Verify property access

You can verify calls to property setters and deleters with [`Verify.set`][decoy.next.Verify.set] and [`Verify.delete`][decoy.next.Verify.delete].

!!! tip

    Use this feature sparingly! If you're designing a dependency that triggers a side-effect, consider using a regular method, instead.

    Mocking and verifying property setters and deleters is most useful for testing code that needs to interact with older or legacy dependencies that would be prohibitively expensive to redesign.

### Verify a setter

Use [`Verify.set`][decoy.next.Verify.set] to check that an attribute was set.

```python
dependency = decoy.mock(name="dependency")

dependency.some_property = 42

decoy.verify(dependency.some_property).set(42)
```

### Verify a deleter

Use [`Verify.delete`][decoy.next.Verify.delete] to check that an attribute was deleted.

```python
dependency = decoy.mock(name="dependency")

del dependency.some_property

decoy.verify(dependency.some_property).delete)
```
