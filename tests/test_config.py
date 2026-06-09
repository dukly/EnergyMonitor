import os
from pathlib import Path
import subprocess
import sys


def test_blank_modbus_device_id_env_uses_profile_default() -> None:
    env = os.environ.copy()
    env['MODBUS_DEVICE_ID'] = ''
    env['PYTHONPATH'] = 'src'

    result = subprocess.run(
        [
            sys.executable,
            '-c',
            'from config import settings; print(settings.modbus_device_id)',
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == 'None'
