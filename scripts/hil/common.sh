#!/usr/bin/env bash
# Shared helpers for the four-panel mosaic hardware-in-the-loop scripts.
# Source this file. Do not execute it directly.
# shellcheck shell=bash

if [[ -n "${HIL_COMMON_LOADED:-}" ]]; then
  return 0
fi
HIL_COMMON_LOADED=1

set -euo pipefail

_HIL_HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${_HIL_HERE}/../.." && pwd)
SLOTS_JSON=${HIL_SLOTS_JSON:-${REPO_ROOT}/ci/expected/slots.json}
CFG_DIR=${HIL_CFG_DIR:-${REPO_ROOT}/hardware/openocd}
HIL_OPENOCD=${HIL_OPENOCD:-openocd}
HIL_OPENOCD_TIMEOUT=${HIL_OPENOCD_TIMEOUT:-240}
HIL_RUN_DIR=${HIL_RUN_DIR:-${HOME}/hil-runs/${GITHUB_RUN_ID:-local}}

hil_prepare() {
  mkdir -p \
    "${HIL_RUN_DIR}/logs" \
    "${HIL_RUN_DIR}/backups" \
    "${HIL_RUN_DIR}/hashes" \
    "${HIL_RUN_DIR}/camera"
}

hil_require_cmd() {
  local cmd=$1
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "required command not found: ${cmd}" >&2
    exit 1
  fi
}

# hil_json_number <field> <hex|dec>
hil_json_number() {
  local field=$1
  local format=$2
  python3 - "${SLOTS_JSON}" "${field}" "${format}" <<'PY'
import json
import sys

path, field, fmt = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, encoding="utf-8") as handle:
    value = json.load(handle)[field]
number = int(value, 0) if isinstance(value, str) else int(value)
print(hex(number) if fmt == "hex" else str(number))
PY
}

# Tab-separated rows: letter, ficr-hex-without-prefix, cfg-filename, tile.
hil_each_slot() {
  python3 - "${SLOTS_JSON}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
order = data.get("order") or list(data["slots"])
for letter in order:
    slot = data["slots"][letter]
    ficr = str(slot["ficr"]).lower().removeprefix("0x")
    print(f"{letter}\t{ficr}\t{slot['cfg']}\t{slot['tile']}")
PY
}

hil_cfg_path() {
  local name=$1
  local path="${CFG_DIR}/${name}"
  if [[ ! -f ${path} ]]; then
    echo "OpenOCD config not found: ${path}" >&2
    exit 1
  fi
  printf '%s\n' "${path}"
}

# hil_openocd <cfg> <tcl-command> [tcl-command...]
# nRESET stays unused: reset_config none, and the checked-in configs leave
# adapter gpio srst commented out. Ports are disabled so a run does not
# collide with the telnet/gdb listeners named in those configs.
hil_openocd() {
  local cfg=$1
  shift
  local -a args=(
    -f "${cfg}"
    -f target/nordic/nrf52.cfg
    -c "tcl_port disabled"
    -c "gdb_port disabled"
    -c "telnet_port disabled"
    -c "reset_config none"
  )
  local command
  for command in "$@"; do
    args+=(-c "${command}")
  done
  timeout "${HIL_OPENOCD_TIMEOUT}" "${HIL_OPENOCD}" "${args[@]}"
}

hil_tee() {
  local log=$1
  shift
  "$@" 2>&1 | tee "${log}"
}

hil_hex_equal() {
  python3 - "$1" "$2" <<'PY'
import sys

sys.exit(0 if int(sys.argv[1], 16) == int(sys.argv[2], 16) else 1)
PY
}
