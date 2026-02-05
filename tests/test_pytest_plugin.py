"""Tests for Decoy's pytest plugin."""

import sys

import pytest


def test_pytest_decoy_fixture(testdir: pytest.Testdir) -> None:
    """It adds a decoy test fixture."""
    testdir.makepyfile(
        """
        from decoy import Decoy

        def test_decoy(decoy):
            assert isinstance(decoy, Decoy)
        """
    )

    result = testdir.runpytest_subprocess()

    result.assert_outcomes(passed=1)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="v3 API required Python >= 3.10")
def test_pytest_decoy_next_fixture(testdir: pytest.Testdir) -> None:
    """It opts into the decoy.next API via annotation."""
    testdir.makepyfile(
        """
        from decoy.next import Decoy

        def test_decoy(decoy: Decoy):
            assert isinstance(decoy, Decoy)
        """
    )

    result = testdir.runpytest_subprocess()

    result.assert_outcomes(passed=1)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="v3 API required Python >= 3.10")
def test_pytest_decoy_next_fixture_fallback(testdir: pytest.Testdir) -> None:
    """It falls back to v2 if annotations are messed up."""
    testdir.makepyfile(
        """
        from decoy import Decoy

        def test_decoy(decoy: 'Oops'):
            assert isinstance(decoy, Decoy)
        """
    )

    result = testdir.runpytest_subprocess()

    result.assert_outcomes(passed=1)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="v3 API required Python >= 3.10")
def test_pytest_decoy_next_fixture_nesting(testdir: pytest.Testdir) -> None:
    """It opts into the decoy.next API via annotation for derived fixtures."""
    testdir.makepyfile(
        """
        import pytest
        from decoy.next import Decoy, Mock

        @pytest.fixture()
        def mock(decoy: Decoy):
            return decoy.mock(name="mock")

        def test_decoy(decoy: Decoy, mock: Mock):
            assert isinstance(mock, Mock)
        """
    )

    result = testdir.runpytest_subprocess()

    result.assert_outcomes(passed=1)
