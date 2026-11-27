#!/usr/bin/env bash
# Read each board's FICR identity word over SWD. Exit non-zero, and do not
# flash, when any board does not match ci/expected/slots.json.
set -euo pipefail

# shellcheck source-path=SCRIPTDIR
# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

hil_prepare
hil_require_cmd python3
hil_require_cmd timeout
hil_require_cmd "${HIL_OPENOCD}"

FICR_ADDR=$(hil_json_number ficr_address hex)
fail=0

while IFS=$'\t' read -r letter ficr cfg tile; do
  cfg_path=$(hil_cfg_path "${cfg}")
  log=${HIL_RUN_DIR}/logs/ficr-${letter}.log
  echo "FICR check board ${letter} tile ${tile} (${cfg})"
  set +e
  hil_tee "${log}" hil_openocd "${cfg_path}" \
    "init" \
    "halt" \
    "mdw ${FICR_ADDR} 1" \
    "shutdown"
  rc=$?
  set -e
  if [[ ${rc} -eq 124 ]]; then
    echo "OpenOCD timed out reading board ${letter}" >&2
    fail=1
    continue
  fi
  if [[ ${rc} -ne 0 ]]; then
    echo "OpenOCD failed reading board ${letter} (exit ${rc})" >&2
    fail=1
    continue
  fi
  if ! got=$(python3 - "${log}" "${FICR_ADDR}" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read().lower()
addr = format(int(sys.argv[2], 0), "x")
match = re.search(r"0x" + addr + r":\s*([0-9a-f]+)", text)
if not match:
    sys.exit(2)
print(match.group(1))
PY
  ); then
    echo "could not parse FICR word for board ${letter} from ${log}" >&2
    fail=1
    continue
  fi
  if hil_hex_equal "${got}" "${ficr}"; then
    echo "board ${letter} FICR ${got} matches"
  else
    echo "board ${letter} FICR mismatch: got ${got}, expected ${ficr}; refusing to flash" >&2
    fail=1
  fi
done < <(hil_each_slot)

if [[ ${fail} -ne 0 ]]; then
  echo "FICR check failed; no board will be programmed" >&2
  exit 1
fi
echo "FICR check passed for every slot"
