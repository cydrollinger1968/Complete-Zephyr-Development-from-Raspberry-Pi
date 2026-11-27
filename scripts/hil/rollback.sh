#!/usr/bin/env bash
# Restore every board that has a local backup. Missing backups are skipped
# so a failure before backup does not invent a restore.
set -euo pipefail

# shellcheck source-path=SCRIPTDIR
# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

hil_prepare
hil_require_cmd python3
hil_require_cmd timeout
hil_require_cmd "${HIL_OPENOCD}"

shopt -s nullglob
backups=("${HIL_RUN_DIR}/backups/"*.bin)
if [[ ${#backups[@]} -eq 0 ]]; then
  echo "no flash backups in ${HIL_RUN_DIR}/backups; nothing to restore"
  exit 0
fi

FLASH_BASE=$(hil_json_number flash_base hex)
fail=0

while IFS=$'\t' read -r letter _ficr cfg _tile; do
  image=${HIL_RUN_DIR}/backups/${letter}.bin
  if [[ ! -s ${image} ]]; then
    echo "no backup for board ${letter}; leaving it untouched"
    continue
  fi
  cfg_path=$(hil_cfg_path "${cfg}")
  log=${HIL_RUN_DIR}/logs/rollback-${letter}.log
  echo "restoring board ${letter} from ${image}"
  set +e
  hil_tee "${log}" hil_openocd "${cfg_path}" \
    "init" \
    "halt" \
    "program ${image} ${FLASH_BASE}" \
    "verify_image ${image} ${FLASH_BASE}" \
    "reset run" \
    "shutdown"
  rc=$?
  set -e
  if [[ ${rc} -ne 0 ]]; then
    echo "restore failed for board ${letter} (exit ${rc})" >&2
    fail=1
  else
    echo "board ${letter} restored"
  fi
done < <(hil_each_slot)

if [[ ${fail} -ne 0 ]]; then
  echo "one or more boards could not be restored; backups remain in ${HIL_RUN_DIR}/backups" >&2
  exit 1
fi
echo "restore finished"
