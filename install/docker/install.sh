#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "${SCRIPT_DIR}/data" "${SCRIPT_DIR}/logs"

if [ ! -f "${SCRIPT_DIR}/.env" ]; then
  cp "${SCRIPT_DIR}/../../.env.example" "${SCRIPT_DIR}/.env"
  echo "Created ${SCRIPT_DIR}/.env from .env.example"
fi

echo "Docker install directory: ${SCRIPT_DIR}"
echo "Edit ${SCRIPT_DIR}/.env and set MODBUS_HOST / INVERTER_PROFILE / MODBUS_DEVICE_ID"
echo "Start with: docker compose -f ${SCRIPT_DIR}/docker-compose.yml up -d --build"
