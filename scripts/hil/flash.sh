#!/usr/bin/env bash
# Program zephyr.hex and verify_image it on every board. Requires a backup
# for each slot so a later failure can be rolled back.
set -euo pipefail

# shellcheck source-path=SCRIPTDIR
# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

hil_prepare
hil_require_cmd python3
hil_require_cmd timeout
hil_require_cmd "${HIL_OPENOCD}"

HEX=${HIL_HEX:-${HIL_RUN_DIR}/zephyr.hex}
if [[ ! -f ${HEX} ]]; then
  echo "hex not found: ${HEX}" >&2
  exit 1
fi

while IFS=$'\t' read -r letter _ficr cfg tile; do
  backup=${HIL_RUN_DIR}/backups/${letter}.bin
  if [[ ! -s ${backup} ]]; then
    echo "refusing to flash board ${letter}: missing backup ${backup}" >&2
    exit 1
  fi
  cfg_path=$(hil_cfg_path "${cfg}")
  log=${HIL_RUN_DIR}/logs/flash-${letter}.log
  echo "flashing board ${letter} tile ${tile}"
  set +e
  hil_tee "${log}" hil_openocd "${cfg_path}" \
    "init" \
    "halt" \
    "program ${HEX}" \
    "verify_image ${HEX}" \
    "reset run" \
    "shutdown"
  rc=$?
  set -e
  if [[ ${rc} -ne 0 ]]; then
    echo "flash or verify_image failed for board ${letter} (exit ${rc})" >&2
    exit 1
  fi
  echo "board ${letter} programmed and verified"
done < <(hil_each_slot)

echo "all boards programmed"
