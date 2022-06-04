"""Simple test suite to ensure Decoy works with unittest."""
import unittest
from decoy import Decoy

from .fixtures import SomeClass


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
        self.decoy.when(mock.foo("hello")).then_return("world")
        assert mock.foo("hello") == "world"

    def test_verify(self) -> None:
        """Test that self.decoy.verify works."""
        mock = self.decoy.mock(cls=SomeClass)
        mock.foo("hello")
        self.decoy.verify(mock.foo("hello"))
