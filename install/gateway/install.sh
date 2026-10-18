#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/energy-monitor-agent}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "Installing EnergyMonitor agent to ${INSTALL_DIR}"

sudo mkdir -p "${INSTALL_DIR}"
sudo cp -r "${REPO_ROOT}/src" "${INSTALL_DIR}/"
if ! sudo test -e "${INSTALL_DIR}/.env"; then
  sudo cp "${REPO_ROOT}/.env.example" "${INSTALL_DIR}/.env"
fi

cd "${INSTALL_DIR}"
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r src/requirements.txt

sudo python3 "${REPO_ROOT}/install/gateway/render_service.py" \
  "${INSTALL_DIR}" /etc/systemd/system/energy-monitor-agent.service
sudo systemctl daemon-reload
sudo systemctl enable energy-monitor-agent

echo "Edit ${INSTALL_DIR}/.env then: sudo systemctl start energy-monitor-agent"
