#!/usr/bin/env bash
# =============================================================================
# Cloud Agent install for "Complete Zephyr Development from Raspberry Pi"
#
# Sets up a Zephyr 4.4 development workspace (west + Zephyr SDK) and builds the
# repository's headline firmware so the environment is proven end-to-end:
#   - MCUboot (RSA-2048 + USB CDC-ACM DFU) for the nRF52840 dongle
#   - the "blinky" sample for the nRF52840 dongle
#   - the "blinky" sample for native_sim (runnable on this x86_64 host)
#
# This complements install100.sh, which targets a physical Raspberry Pi 5 with
# GPIO SWD + OpenOCD hardware flashing. Those hardware/flashing steps (OpenOCD
# build, gpiochip wiring, sudoers, group membership) are intentionally omitted
# here because a Cloud Agent VM has no Nordic hardware attached.
#
# The script is idempotent: it can be re-run safely and converges without
# re-downloading or rewriting state that already exists.
# =============================================================================

set -euo pipefail

INSTALL_DIR="${ZEPHYR_INSTALL_DIR:-$HOME/zephyrproject}"
ZEPHYR_REV="${ZEPHYR_REV:-v4.4.0}"

echo "=== Zephyr Cloud Agent setup ==="
echo "Workspace : $INSTALL_DIR"
echo "Zephyr rev: $ZEPHYR_REV"

# ----------------------------- System dependencies -----------------------------
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
    cmake ninja-build gperf ccache dfu-util device-tree-compiler \
    python3-dev python3-pip python3-venv python3-setuptools python3-wheel \
    git curl wget xz-utils file \
    build-essential gcc-multilib g++-multilib libtool autoconf automake pkg-config \
    libusb-1.0-0-dev libhidapi-dev libgpiod-dev gpiod

# ----------------------------- Python venv + west -----------------------------
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install west

# ----------------------------- West workspace -----------------------------
if [ ! -f ".west/config" ]; then
    west init -m https://github.com/zephyrproject-rtos/zephyr --mr "$ZEPHYR_REV"
fi
west update --narrow

pip install -r zephyr/scripts/requirements.txt
pip install -r bootloader/mcuboot/scripts/requirements.txt

# ----------------------------- Zephyr SDK -----------------------------
west zephyr-export
if ! ls -d "$HOME"/zephyr-sdk-* >/dev/null 2>&1 && [ ! -d /opt/zephyr-sdk ]; then
    west sdk install
else
    echo "Zephyr SDK already installed; skipping download."
fi

# ----------------------------- Firmware builds -----------------------------
# MCUboot for the nRF52840 dongle (RSA-2048 + USB CDC-ACM recovery), matching
# install100.sh's MCUboot configuration.
west build -b nrf52840dongle/nrf52840/bare \
    bootloader/mcuboot/boot/zephyr \
    -d build/mcuboot_bare \
    --force \
    -- \
    -DCONFIG_BOOT_SIGNATURE_TYPE_RSA=y \
    -DCONFIG_BOOT_SIGNATURE_TYPE_RSA_LEN=2048 \
    -DCONFIG_BOOT_IMG_HASH_ALG_SHA256=y \
    -DCONFIG_BOOT_ERASE_PROGRESSIVELY=y \
    -DCONFIG_BOOT_SWAP_USING_MOVE=y \
    -DCONFIG_BOOT_MAX_IMG_SECTORS=256 \
    -DOVERLAY_CONFIG=usb_cdc_acm_recovery.conf

# blinky application image for the real nRF52840 dongle target.
west build -b nrf52840dongle/nrf52840 zephyr/samples/basic/blinky \
    -d build/blinky_dongle --force

# blinky built for native_sim so it can be executed directly on this host.
west build -b native_sim zephyr/samples/basic/blinky \
    -d build/blinky_sim --force

echo "=== Setup complete ==="
echo "Activate with: source $INSTALL_DIR/.venv/bin/activate"
echo "Run blinky (native_sim): $INSTALL_DIR/build/blinky_sim/zephyr/zephyr.exe"
