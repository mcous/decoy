"""Tests for Decoy's pytest plugin."""

import pytest


def test_pytest_decoy_fixture(testdir: pytest.Testdir) -> None:
    """It should add a decoy test fixture."""
    # create a temporary pytest test file
    testdir.makepyfile(
        """
        from decoy import Decoy

        def test_decoy(decoy):
            assert isinstance(decoy, Decoy)
        """
    )

    result = testdir.runpytest()

    # check that all 4 tests passed
    result.assert_outcomes(passed=1)
