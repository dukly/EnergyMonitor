import os
from pathlib import Path
import subprocess
import sys


def test_blank_modbus_device_id_uses_profile_default() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env['MODBUS_DEVICE_ID'] = ''
    env['PYTHONPATH'] = str(repo_root / 'src')

    result = subprocess.run(
        [
            sys.executable,
            '-c',
            'from config import settings\nprint(settings.modbus_device_id)\n',
        ],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'None'
