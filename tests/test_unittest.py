"""Simple test suite to ensure Decoy works with unittest."""

from __future__ import annotations

import sys
import unittest

import pytest

from .fixtures import SomeClass

if sys.version_info >= (3, 10):
    from decoy.next import Decoy

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="v3 preview only supports Python >= 3.10",
)


class DecoyTestCase(unittest.TestCase):
    """Decoy test case using unittest."""

    def setUp(self) -> None:
        """Set up before each test."""
        self.decoy = Decoy()

    def tearDown(self) -> None:
        """Clean up after each test."""
        self.decoy.reset()

    def test_when(self) -> None:
        """Test that self.decoy.when works."""
        mock = self.decoy.mock(cls=SomeClass)
        self.decoy.when(mock.foo).called_with("hello").then_return("world")
        assert mock.foo("hello") == "world"

    def test_verify(self) -> None:
        """Test that self.decoy.verify works."""
        mock = self.decoy.mock(cls=SomeClass)
        mock.foo("hello")
        self.decoy.verify(mock.foo).called_with("hello")
