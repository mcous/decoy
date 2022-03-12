# Mocking property attributes

Python [property attributes][] provide an interface for creating read-only properties and properties with getters, setters, and deleters. You can use Decoy to stub properties and verify calls to property setters and deleters.

[property attributes]: https://docs.python.org/3/library/functions.html#property

## Default behavior

Unlike mock method calls - which have a default return value of `None` - Decoy's default return value for attribute access is **another mock**. So you don't need to configure anything explicitly if you need a `@property` getter to return another mock; Decoy will do this for you.

```python
class SubDep:
    ...

class Dep:
    @property
    def sub(self) -> SubDep:
        ...

def test(decoy: Decoy) -> None:
    dep = decoy.mock(cls=Dep)  # <- mock of class Dep
    sub = dep.sub              # <- mock of class SubDep
    ...
```

## Stubbing property access

### Stubbing a getter

If you would like to stub a return value for a property that is different than the default behavior, simply use the property itself as your rehearsal.

```python
dep = decoy.mock()

decoy.when(
    dep.some_property  # <- "rehearsal" of a property getter
).then_return(42)

assert dep.some_property == 42
```

You can also configure any other stubbing, like raising an error.

```python
dep = decoy.mock()

decoy.when(
    dep.some_property
).then_raise(RuntimeError("oh no"))

with pytest.raises(RuntimeError, match="oh no"):
    dep.some_property
```

### Stubbing a setter or deleter

While you cannot stub a return value for a getter or setter, you can stub a `raise` or a side effect by combining [decoy.Decoy.when][] with [decoy.Decoy.prop][].

The `prop` method allows you to create rehearsals of setters and deleters. Use [decoy.Prop.set][] to create a setter rehearsal, and [decoy.Prop.delete][] to create a deleter rehearsal.

```python
dep = decoy.mock()

decoy.when(
    decoy.prop(dep.some_property).set(42)
).then_return(RuntimeError("oh no"))

decoy.when(
    decoy.prop(dep.some_property).delete()
).then_return(RuntimeError("what a disaster"))

with pytest.raises(RuntimeError, match="oh no"):
    dep.some_property = 42

with pytest.raises(RuntimeError, match="what a disaster"):
    del dep.some_property
```

!!! tip

    You cannot use [decoy.Stub.then_return][] with property setters and deleters, because set and delete expressions do not return a value in Python.

## Verifying property access

You can verify calls to property setters and deleters by combining [decoy.Decoy.verify][] with [decoy.Decoy.prop][], the same way you would configure a stub.

**Use this feature sparingly!** If you're designing a dependency that triggers a side-effect, consider using a regular method rather than a property setter/deleter. It'll probably make your code easier to read and reason with.

Mocking and verifying property setters and deleters is most useful for testing code that needs to interact with older or legacy dependencies that would be prohibitively expensive to redesign.

!!! tip

    You cannot verify getters with `Decoy.verify`. The `verify` method is for verifying side-effects, and it is the opinion of the author that property getters should not trigger side-effects. Getter-triggered side effects are confusing and do not communicate the design intent of a system.

### Verifying a setter

Use [decoy.Prop.set][] to create a setter rehearsal to use in [decoy.Decoy.verify][].

```python
dep = decoy.mock()

dep.some_property = 42

decoy.verify(
    decoy.prop(dep.some_property).set(42)  # <- "rehearsal" of a property setter
)
```

### Verifying a deleter

Use [decoy.Prop.delete][] to create a deleter rehearsal to use in [decoy.Decoy.verify][].

```python
dep = decoy.mock()

del dep.some_property

decoy.verify(
    decoy.prop(dep.some_property).delete()  # <- "rehearsal" of a property deleter
)
```

## Example

In this example, we're developing a `Core` unit, with a `Config` dependency. We want to test that we get, set, and delete the `port` property of the `Config` dependency when various methods of `Core` are used.

```python
from decoy import Decoy


class InvalidPortValue(ValueError):
    """Exception raised when a given port value is invalid."""


class Config:
    """Config dependency."""

    @property
    def port(self) -> int:
        ...

    @port.setter
    def port(self) -> None:
        ...

    @port.deleter
    def port(self) -> None:
        ...


class Core:
    """Core test subject."""

    def __init__(self, config: Config) -> None:
        self._config = config

    def get_port(self) -> int:
        return self._config.port

    def set_port(self, port: int) -> None:
        try:
            self._config.port = port
        except ValueError as e:
            raise InvalidPortValue(str(e)) from e

    def reset_port(self) -> None:
        del self._config.port


def test_gets_port(decoy: Decoy) -> None:
    """Core should get the port number from its Config dependency."""
    config = decoy.mock(cls=Config)
    subject = Core(config=config)

    decoy.when(
        config.port  # <- "rehearsal" of a property getter
    ).then_return(42)

    result = subject.get_port()

    assert result == 42


def test_rejects_invalid_port(decoy: Decoy) -> None:
    """Core should re-raise if the port number is set to an invalid value."""
    config = decoy.mock(cls=Config)
    subject = Core(config=config)

    decoy.when(
        decoy.prop(config.port).set(9001)  # <- "rehearsal" of a property setter
    ).then_raise(ValueError("there's no way that can be right"))

    with pytest.raises(InvalidPortValue, "there's no way"):
        subject.set_port(9001)


def test_sets_port(decoy: Decoy) -> None:
    """Core should set the port number in its Config dependency."""
    config = decoy.mock(cls=Config)
    subject = Core(config=config)

    subject.set_port(101)

    decoy.verify(
        decoy.prop(config.port).set(101)  # <- "rehearsal" of a property setter
    )

def test_resets_port(decoy: Decoy) -> None:
    """Core should delete the port number in its Config dependency."""
    config = decoy.mock(cls=Config)
    subject = Core(config=config)

    subject.reset_port()

    decoy.verify(
        decoy.prop(config.port).delete()  # <- "rehearsal" of a property deleter
    )
```
