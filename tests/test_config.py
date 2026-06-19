import os
import subprocess
import sys


def test_blank_modbus_device_id_uses_profile_default(tmp_path) -> None:
    env = os.environ.copy()
    env['PYTHONPATH'] = 'src'
    env['MODBUS_DEVICE_ID'] = ''
    env['LOG_FILE_PATH'] = str(tmp_path / 'monitor.log')
    env['ERROR_LOG_FILE_PATH'] = str(tmp_path / 'error.log')

    result = subprocess.run(
        [
            sys.executable,
            '-c',
            'from config import settings; print(settings.modbus_device_id)',
        ],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip() == 'None'
