"""Render systemd paths for the actual installation directory."""

import sys
from pathlib import Path, PurePosixPath


def render_service(install_dir: str) -> str:
    if not PurePosixPath(install_dir).is_absolute() or any(ord(char) < 32 for char in install_dir):
        raise ValueError('INSTALL_DIR must be an absolute path without control characters')
    path = str(PurePosixPath(install_dir))
    # systemd specifiers and quoted string syntax; this is not shell quoting.
    escaped = path.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%')
    template = Path(__file__).with_name('energy-monitor-agent.service').read_text(encoding='utf-8')
    rendered = template.replace('/opt/energy-monitor-agent', escaped)
    # Only command lines perform environment-variable expansion in systemd.
    return '\n'.join(
        line.replace('$', '$$') if line.startswith('ExecStart=') else line
        for line in rendered.splitlines()
    ) + '\n'


if __name__ == '__main__':
    Path(sys.argv[2]).write_text(render_service(sys.argv[1]), encoding='utf-8')
