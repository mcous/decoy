"""Tests for Decoy's pytest plugin."""
from pytest import Testdir


def test_pytest_decoy_fixture(testdir: Testdir) -> None:
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
