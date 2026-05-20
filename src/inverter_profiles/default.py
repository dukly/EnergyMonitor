from inverter_profiles.base import InverterProfile

PROFILE = InverterProfile(
    name='default',
    register_start=32000,
    register_count=20,
    device_id=1,
    description='Generic map (32000–32019)',
)
