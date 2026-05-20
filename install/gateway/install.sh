#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/sunhors-agent}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "Installing sunhors-agent to ${INSTALL_DIR}"

sudo mkdir -p "${INSTALL_DIR}"
sudo cp -r "${REPO_ROOT}/src" "${INSTALL_DIR}/"
sudo cp "${REPO_ROOT}/.env.example" "${INSTALL_DIR}/.env" 2>/dev/null || true

cd "${INSTALL_DIR}"
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r src/requirements.txt

sudo cp "${REPO_ROOT}/install/gateway/sunhors-agent.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sunhors-agent

echo "Edit ${INSTALL_DIR}/.env then: sudo systemctl start sunhors-agent"
