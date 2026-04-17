#!/usr/bin/env bash

smarthub_uname_s() {
  if [ -n "${SMARTHUB_TEST_UNAME:-}" ]; then
    printf '%s\n' "$SMARTHUB_TEST_UNAME"
    return
  fi

  uname -s
}

smarthub_detect_platform() {
  case "$(smarthub_uname_s)" in
    Linux)
      printf 'linux\n'
      ;;
    Darwin)
      printf 'macos\n'
      ;;
    *)
      printf 'unsupported\n'
      ;;
  esac
}

smarthub_platform_label() {
  case "${1:-$(smarthub_detect_platform)}" in
    linux)
      printf 'Linux/Raspberry Pi\n'
      ;;
    macos)
      printf 'macOS Docker Desktop\n'
      ;;
    *)
      printf 'unsupported\n'
      ;;
  esac
}

smarthub_compose_files() {
  case "$(smarthub_detect_platform)" in
    linux)
      printf 'docker-compose.yml docker-compose.linux.yml\n'
      ;;
    macos)
      printf 'docker-compose.yml docker-compose.macos.yml\n'
      ;;
    *)
      return 1
      ;;
  esac
}

smarthub_ha_port() {
  if [ -n "${HA_PORT:-}" ]; then
    printf '%s\n' "$HA_PORT"
    return
  fi

  if [ -n "${HA_URL:-}" ]; then
    python3 - "$HA_URL" <<'PY'
import sys
from urllib.parse import urlparse

parsed = urlparse(sys.argv[1])
print(parsed.port or 8123)
PY
    return
  fi

  printf '8123\n'
}

smarthub_default_ha_origin() {
  local ha_port
  ha_port="$(smarthub_ha_port)"

  case "$(smarthub_detect_platform)" in
    linux)
      printf 'http://homeassistant.local:%s\n' "$ha_port"
      ;;
    macos)
      printf 'http://localhost:%s\n' "$ha_port"
      ;;
    *)
      return 1
      ;;
  esac
}

smarthub_port_in_use() {
  if [ -n "${SMARTHUB_TEST_BUSY_PORTS:-}" ]; then
    local busy_port
    IFS=',' read -r -a busy_ports <<<"$SMARTHUB_TEST_BUSY_PORTS"
    for busy_port in "${busy_ports[@]}"; do
      if [ "$busy_port" = "$1" ]; then
        return 0
      fi
    done
    return 1
  fi

  python3 - "$1" <<'PY'
import socket
import sys

port = int(sys.argv[1])
for host in ("127.0.0.1", "localhost"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        if sock.connect_ex((host, port)) == 0:
            raise SystemExit(0)

raise SystemExit(1)
PY
}
