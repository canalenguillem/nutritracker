#!/usr/bin/env sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
environment_file="${ENV_FILE:-${project_dir}/.env}"

if [ -f "$environment_file" ]; then
  set -a
  # The project environment file uses shell-compatible KEY=VALUE assignments.
  . "$environment_file"
  set +a
fi

base_url="${APP_URL:-http://localhost}"
api_prefix="${API_V1_PREFIX:-/api/v1}"
n8n_url="${N8N_URL:-http://localhost:5679}"
phpmyadmin_port="${PHPMYADMIN_PORT:-8081}"

check_url() {
  name="$1"
  url="$2"

  if curl --fail --silent --show-error "$url" >/dev/null; then
    printf '%s: healthy\n' "$name"
    return 0
  fi

  printf '%s: unhealthy (%s)\n' "$name" "$url" >&2
  return 1
}

check_url "Application" "${base_url}/"
check_url "Backend readiness" "${base_url}${api_prefix}/health/ready"
check_url "Nginx" "${base_url}/nginx-health"
check_url "n8n" "${n8n_url}/healthz"
check_url "phpMyAdmin" "http://localhost:${phpmyadmin_port}/"
