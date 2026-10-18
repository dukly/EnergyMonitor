import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('render_service', ROOT / 'install/gateway/render_service.py')
service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service_module)


def test_systemd_uses_actual_install_directory():
    text = service_module.render_service('/srv/energy monitor')
    assert 'WorkingDirectory="/srv/energy monitor"' in text
    assert 'ExecStart="/srv/energy monitor/venv/bin/python" "/srv/energy monitor/src/main.py"' in text
    assert '/opt/energy-monitor-agent' not in text
    # Pydantic reads the single .env consistently on all platforms, including BOM files.
    assert 'EnvironmentFile=' not in text


def test_systemd_escapes_specifiers_and_command_variables():
    text = service_module.render_service('/srv/monitor%name$HOME')
    assert 'WorkingDirectory="/srv/monitor%%name$HOME"' in text
    assert 'ExecStart="/srv/monitor%%name$$HOME/venv/bin/python"' in text


@pytest.mark.parametrize('path', ['relative/path', '/tmp/\nExecStart=bad', '/tmp/\x00bad'])
def test_systemd_rejects_invalid_paths(path):
    with pytest.raises(ValueError):
        service_module.render_service(path)


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows installer needs PowerShell on Windows')
@pytest.mark.parametrize('shell', ['powershell', 'pwsh'])
def test_windows_installation_and_upgrade(shell):
    executable = shutil.which(shell)
    if executable is None:
        pytest.skip(f'{shell} is not installed')
    result = subprocess.run(
        [executable, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
         str(ROOT / 'tests/test_windows_install.ps1'), '-PythonExe', sys.executable],
        capture_output=True, text=True, timeout=30,
        env={key.upper(): value for key, value in os.environ.items()},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS:' in result.stdout


def test_gateway_installer_preserves_config_on_upgrade(tmp_path):
    # Run the real installer, substituting only privileged/service/package commands.
    # Linux CI uses bash; Windows can supply BusyBox ash for its POSIX shell logic.
    busybox = os.environ.get('ENERGYMONITOR_TEST_BUSYBOX')
    if busybox:
        shell = [busybox, 'sh']
    elif sys.platform != 'win32' and shutil.which('bash'):
        shell = [shutil.which('bash')]
    else:
        pytest.skip('Needs bash or ENERGYMONITOR_TEST_BUSYBOX')
    repo = tmp_path / 'repo'
    shutil.copytree(ROOT / 'install/gateway', repo / 'install/gateway')
    (repo / 'src').mkdir()
    (repo / 'src/main.py').write_text('first', encoding='utf-8')
    (repo / '.env.example').write_text('MODBUS_HOST=initial\n', encoding='utf-8')
    install = tmp_path / 'custom install'
    environment = {
        **os.environ, 'INSTALL_DIR': install.as_posix(),
        'RENDER_ARGS': (tmp_path / 'render-args.txt').as_posix(),
    }
    harness = '''
sudo() {
    case "$1" in
        python3)
            if [ "$2" = "-m" ]; then
                return 0
            fi
            printf '%s' "$3" > "$RENDER_ARGS"
            return 0
            ;;
        ./venv/bin/pip|systemctl) return 0 ;;
        mkdir|cp|test) "$@" ;;
        *) echo "Unexpected privileged operation: $*" >&2; return 1 ;;
    esac
}
. "$0"
'''

    def run_installer():
        result = subprocess.run(
            [*shell, '-c', harness, (repo / 'install/gateway/install.sh').as_posix()],
            env=environment, capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    run_installer()
    assert (install / 'src/main.py').read_text() == 'first'
    assert (install / '.env').read_text() == 'MODBUS_HOST=initial\n'
    custom = b'\xef\xbb\xbfMODBUS_HOST=custom\r\nMODBUS_TIMEOUT=17\r\n'
    (install / '.env').write_bytes(custom)
    (install / 'data').mkdir()
    (install / 'data/monitor.db').write_bytes(b'existing data')
    (repo / 'src/main.py').write_text('updated', encoding='utf-8')
    run_installer()
    assert (install / 'src/main.py').read_text() == 'updated'
    assert (install / '.env').read_bytes() == custom
    assert (install / 'data/monitor.db').read_bytes() == b'existing data'
    assert not (install / 'src/src').exists()
    assert (tmp_path / 'render-args.txt').read_text() == install.as_posix()
