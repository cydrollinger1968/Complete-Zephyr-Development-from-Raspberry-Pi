#!/usr/bin/env bash
# Pristine west build of one mosaic app. The hex is copied into the run dir.
set -euo pipefail

# shellcheck source-path=SCRIPTDIR
# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

hil_prepare
hil_require_cmd python3

HIL_APP=${HIL_APP:-mosaic_block_diagram}
HIL_BOARD=${HIL_BOARD:-nrf52dk/nrf52832}
EINK_APPS_DIR=${EINK_APPS_DIR:-${HOME}/zephyrproject/apps}

if [[ ! ${HIL_APP} =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "app name must be a single directory name, got: ${HIL_APP}" >&2
  exit 1
fi
if [[ ! ${HIL_BOARD} =~ ^[A-Za-z0-9._/-]+$ || ${HIL_BOARD} == *..* ]]; then
  echo "board name is not a west board id: ${HIL_BOARD}" >&2
  exit 1
fi
if [[ ${EINK_APPS_DIR} != /* || ${EINK_APPS_DIR} == *..* || ${EINK_APPS_DIR} == *$'\n'* ]]; then
  echo "EINK_APPS_DIR must be an absolute path without '..'" >&2
  exit 1
fi

APP_DIR=${EINK_APPS_DIR}/${HIL_APP}
if [[ ! -d ${APP_DIR} ]]; then
  echo "app directory not found: ${APP_DIR}" >&2
  exit 1
fi

WORKSPACE=${HOME}/zephyrproject
if [[ -f ${WORKSPACE}/.venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source "${WORKSPACE}/.venv/bin/activate"
fi

if [[ -z ${WEST:-} ]]; then
  if [[ -x ${WORKSPACE}/.venv/bin/west ]]; then
    WEST=${WORKSPACE}/.venv/bin/west
  else
    WEST=west
  fi
fi
hil_require_cmd "${WEST}"

BUILD_DIR=${HIL_RUN_DIR}/build
echo "west build -p always -b ${HIL_BOARD} ${APP_DIR}"
(
  cd "${WORKSPACE}"
  hil_tee "${HIL_RUN_DIR}/logs/build.log" \
    "${WEST}" build -p always -b "${HIL_BOARD}" -d "${BUILD_DIR}" "${APP_DIR}"
)

HEX=""
for candidate in \
  "${BUILD_DIR}/zephyr/zephyr.signed.hex" \
  "${BUILD_DIR}/zephyr/zephyr.hex"
do
  if [[ -f ${candidate} ]]; then
    HEX=${candidate}
    break
  fi
done
if [[ -z ${HEX} ]]; then
  echo "build finished without zephyr.hex or zephyr.signed.hex" >&2
  exit 1
fi

install -m 0644 "${HEX}" "${HIL_RUN_DIR}/zephyr.hex"
sha256sum "${HIL_RUN_DIR}/zephyr.hex" | tee "${HIL_RUN_DIR}/hashes/zephyr.hex.sha256"
{
  echo "app=${HIL_APP}"
  echo "board=${HIL_BOARD}"
  echo "hex_source=$(basename "${HEX}")"
} >"${HIL_RUN_DIR}/hashes/build.txt"
echo "built ${HIL_RUN_DIR}/zephyr.hex"
