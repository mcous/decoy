from typing import Protocol, TypeVar

EnterValueT = TypeVar("EnterValueT", covariant=True)


class HasEnter(Protocol[EnterValueT]):
    def __enter__(self) -> EnterValueT: ...
