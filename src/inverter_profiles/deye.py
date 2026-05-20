from inverter_profiles.base import InverterProfile

PROFILE = InverterProfile(
    name='deye',
    register_start=32000,
    register_count=20,
    device_id=1,
    description='Deye hybrid/string (standard input block)',
)
