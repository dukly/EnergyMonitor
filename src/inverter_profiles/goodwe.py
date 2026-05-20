from inverter_profiles.base import InverterProfile

PROFILE = InverterProfile(
    name='goodwe',
    register_start=32000,
    register_count=20,
    device_id=1,
    description='GoodWe ET/MT series (adjust per firmware if needed)',
)
