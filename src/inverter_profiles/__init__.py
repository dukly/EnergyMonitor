from inverter_profiles.base import InverterProfile
from inverter_profiles.deye import PROFILE as DEYE_PROFILE
from inverter_profiles.goodwe import PROFILE as GOODWE_PROFILE
from inverter_profiles.default import PROFILE as DEFAULT_PROFILE

PROFILES: dict[str, InverterProfile] = {
    'default': DEFAULT_PROFILE,
    'deye': DEYE_PROFILE,
    'goodwe': GOODWE_PROFILE,
}


def get_profile(name: str) -> InverterProfile:
    key = name.strip().lower()
    if key not in PROFILES:
        raise ValueError(f'Unknown inverter profile: {name}. Available: {", ".join(PROFILES)}')
    return PROFILES[key]
