#!/usr/bin/env bash
# Optional optical check. Uses $HOME/capture_avg when that tool exists.
# A missing tool is a skip, not a failure. A failing tool is a failure.
set -euo pipefail

# shellcheck source-path=SCRIPTDIR
# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

hil_prepare

TOOL=${HOME}/capture_avg
FRAMES=${HIL_CAMERA_FRAMES:-4}
SHUTTER=${HIL_CAMERA_SHUTTER:-}
GAIN=${HIL_CAMERA_GAIN:-}

if [[ ! -e ${TOOL} ]]; then
  echo "capture_avg is not present; camera verification skipped"
  echo "skipped: capture_avg missing" >"${HIL_RUN_DIR}/camera/SKIPPED.txt"
  exit 0
fi
if [[ ! -x ${TOOL} ]]; then
  echo "capture_avg is not executable; camera verification skipped"
  echo "skipped: capture_avg not executable" >"${HIL_RUN_DIR}/camera/SKIPPED.txt"
  exit 0
fi
if [[ ! ${FRAMES} =~ ^[1-9][0-9]*$ ]]; then
  echo "camera frame count must be a positive integer" >&2
  exit 1
fi
if [[ -n ${SHUTTER} && ! ${SHUTTER} =~ ^[0-9]+$ ]]; then
  echo "camera shutter must be an integer" >&2
  exit 1
fi
if [[ -n ${GAIN} && ! ${GAIN} =~ ^[0-9]+$ ]]; then
  echo "camera gain must be an integer" >&2
  exit 1
fi

STACK=${HOME}/oc_stack
mkdir -p "${STACK}"
before=$(date +%s)
args=("${FRAMES}")
if [[ -n ${SHUTTER} ]]; then
  args+=("${SHUTTER}")
  if [[ -n ${GAIN} ]]; then
    args+=("${GAIN}")
  fi
fi

echo "running capture_avg ${args[*]}"
hil_tee "${HIL_RUN_DIR}/logs/camera.log" "${TOOL}" "${args[@]}"

newest=""
newest_mtime=0
while IFS= read -r dir; do
  [[ -d ${dir} ]] || continue
  mtime=$(stat -c '%Y' "${dir}")
  if [[ ${mtime} -ge ${before} && ${mtime} -ge ${newest_mtime} ]]; then
    newest=${dir}
    newest_mtime=${mtime}
  fi
done < <(find "${STACK}" -mindepth 1 -maxdepth 1 -type d)

if [[ -z ${newest} ]]; then
  echo "capture_avg did not create a directory under ${STACK}" >&2
  exit 1
fi

echo "camera output ${newest}"
copied=0
while IFS= read -r -d '' file; do
  rel=${file#"${newest}/"}
  safe=${rel//\//__}
  cp "${file}" "${HIL_RUN_DIR}/camera/${safe}"
  copied=$((copied + 1))
done < <(find "${newest}" -type f \
  \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \
     -o -iname '*.txt' -o -iname '*.log' -o -iname '*.json' \
     -o -iname '*.md' -o -iname '*.csv' \) -print0)

if [[ ${copied} -eq 0 ]]; then
  echo "no images or report files in ${newest}" >&2
  exit 1
fi
echo "copied ${copied} camera files into ${HIL_RUN_DIR}/camera"
