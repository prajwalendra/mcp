import pytest


def test_exception_raised():
    """Test that exceptions can be caught by pytest.raises."""
    with pytest.raises(ValueError):
        raise ValueError('This is a test exception')
