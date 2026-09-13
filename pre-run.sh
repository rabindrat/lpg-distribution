#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python}"
MANAGE_PY="${MANAGE_PY:-manage.py}"

echo "Applying database migrations..."
"$PYTHON_BIN" "$MANAGE_PY" migrate --noinput

echo "Seeding LPG brands..."
"$PYTHON_BIN" "$MANAGE_PY" seed_brands

echo "Seeding LPG companies and brand links..."
"$PYTHON_BIN" "$MANAGE_PY" seed_companies

echo "Seeding dealer directory..."
"$PYTHON_BIN" "$MANAGE_PY" seed_dealers

if [[ "${SEED_DEMO_DATA:-false}" == "true" ]]; then
  echo "Seeding staging demo data..."
  "$PYTHON_BIN" "$MANAGE_PY" seed_demo_data
else
  echo "Skipping staging demo data (set SEED_DEMO_DATA=true to enable)."
fi

echo "Collecting static assets..."
"$PYTHON_BIN" "$MANAGE_PY" collectstatic --noinput

echo "Pre-run setup completed."
