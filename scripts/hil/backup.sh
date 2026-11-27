#!/usr/bin/env bash
# Dump each board's flash into the local run directory. These files stay on
# the rig Pi and are not uploaded.
set -euo pipefail

# shellcheck source-path=SCRIPTDIR
# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

hil_prepare
hil_require_cmd python3
hil_require_cmd timeout
hil_require_cmd "${HIL_OPENOCD}"

FLASH_BASE=$(hil_json_number flash_base hex)
if [[ -n ${HIL_FLASH_BYTES:-} ]]; then
  FLASH_BYTES=$(python3 - "${HIL_FLASH_BYTES}" <<'PY'
import sys
print(int(sys.argv[1], 0))
PY
)
else
  FLASH_BYTES=$(hil_json_number flash_bytes dec)
fi

: >"${HIL_RUN_DIR}/hashes/backups.sha256"

while IFS=$'\t' read -r letter _ficr cfg _tile; do
  cfg_path=$(hil_cfg_path "${cfg}")
  image=${HIL_RUN_DIR}/backups/${letter}.bin
  log=${HIL_RUN_DIR}/logs/backup-${letter}.log
  echo "backing up board ${letter} (${FLASH_BYTES} bytes) to ${image}"
  set +e
  hil_tee "${log}" hil_openocd "${cfg_path}" \
    "init" \
    "halt" \
    "dump_image ${image} ${FLASH_BASE} ${FLASH_BYTES}" \
    "shutdown"
  rc=$?
  set -e
  if [[ ${rc} -ne 0 || ! -s ${image} ]]; then
    echo "backup failed for board ${letter} (exit ${rc})" >&2
    exit 1
  fi
  sha256sum "${image}" >>"${HIL_RUN_DIR}/hashes/backups.sha256"
done < <(hil_each_slot)

echo "flash backups are in ${HIL_RUN_DIR}/backups (local only)"
