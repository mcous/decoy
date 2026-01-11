"""Tests for stringification utilities."""

from decoy.spy_events import PropAccessType, SpyEvent, SpyInfo, SpyPropAccess
from decoy.stringify import stringify_call


def test_spy_call_stringifies() -> None:
    """It serializes a property get event."""
    assert (
        stringify_call(
            SpyEvent(
                spy=SpyInfo(id=42, name="some", is_async=False),
                payload=SpyPropAccess(prop_name="name", access_type=PropAccessType.GET),
            )
        )
        == "some.name"
    )
