from dataclasses import dataclass


@dataclass(frozen=True)
class InverterProfile:
    """Modbus register map for a specific inverter family."""

    name: str
    register_start: int
    register_count: int
    device_id: int = 1
    description: str = ''
