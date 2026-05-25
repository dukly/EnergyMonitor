from inverter_profiles.base import InverterProfile

PROFILE = InverterProfile(
    name='deye',
    register_start=32000,
    register_count=20,
    device_id=1,
    register_kind='auto',
    description='Deye / Sunsynk (auto: holding FC03, then input FC04)',
)
