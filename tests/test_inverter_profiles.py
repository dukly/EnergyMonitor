import pytest

from inverter_profiles import get_profile


def test_get_profile_deye() -> None:
    profile = get_profile('deye')
    assert profile.name == 'deye'
    assert profile.register_start == 32000


def test_unknown_profile_raises() -> None:
    with pytest.raises(ValueError):
        get_profile('unknown-brand')
