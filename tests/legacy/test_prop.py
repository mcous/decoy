"""Tests for decoy.prop."""

import pytest

from decoy import Decoy
from decoy.errors import MissingRehearsalError

from ..fixtures import SomeClass


def test_property_missing_rehearsal(decoy: Decoy) -> None:
    """It raises an error if no prop rehearsal."""
    with pytest.raises(MissingRehearsalError):
        decoy.prop("42")


def test_property_missing_rehearsal_after_success(decoy: Decoy) -> None:
    """It raises an error if no prop rehearsal after a successful rehearsal."""
    subject = decoy.mock(cls=SomeClass)

    decoy.prop(subject.primitive_property)

    with pytest.raises(MissingRehearsalError):
        decoy.prop("42")
