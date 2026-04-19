#!/usr/bin/env bash
# =============================================================================
# Hardened Zephyr 4.4 + MCUboot (RSA-2048 + USB CDC-ACM DFU) Setup for nRF52840
# Version: 2026-04 Improved (Repeatable + Passwordless sudo during install)
# =============================================================================

set -euo pipefail

# ----------------------------- Configuration -----------------------------
INSTALL_DIR="${ZEPHYR_INSTALL_DIR:-$HOME/zephyrproject}"
ZEPHYR_REV="v4.4.0"
MCU_BOOT_BUILD_DIR="$INSTALL_DIR/build/mcuboot_bare"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Zephyr 4.4 + MCUboot Setup for nRF52840 Dongle ===${NC}"
echo "Install dir : $INSTALL_DIR"
echo "Zephyr rev  : $ZEPHYR_REV"
echo ""

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}" >&2; }

# ----------------------------- One-time Passwordless sudo Setup -----------------------------
echo -e "${BLUE}Setting up passwordless sudo for installation commands...${NC}"

SUDOERS_FILE="/etc/sudoers.d/zephyr-install-$USER"

cat << EOF | sudo tee "$SUDOERS_FILE" > /dev/null
# Passwordless sudo for Zephyr + OpenOCD installation (limited & specific)
$USER ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/apt
$USER ALL=(ALL) NOPASSWD: /usr/bin/make
$USER ALL=(ALL) NOPASSWD: /usr/local/bin/openocd
$USER ALL=(ALL) NOPASSWD: /usr/sbin/usermod
$USER ALL=(ALL) NOPASSWD: /usr/bin/groupadd, /usr/bin/chown
EOF

sudo chmod 0440 "$SUDOERS_FILE"
print_success "Passwordless sudo configured for this installation"

# ----------------------------- Prerequisites -----------------------------
echo -e "${BLUE}Installing system dependencies...${NC}"
sudo apt update -qq
sudo apt install -y --no-install-recommends \
    cmake ninja-build gperf ccache dfu-util device-tree-compiler \
    python3-dev python3-pip python3-venv git curl wget \
    build-essential libtool autoconf automake pkg-config \
    libusb-1.0-0-dev libhidapi-dev libgpiod-dev gpiod

# Add user to groups (idempotent)
sudo usermod -aG gpio,dialout "$USER" 2>/dev/null || true
print_success "Dependencies installed and groups updated"

# ----------------------------- Workspace Setup -----------------------------
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Python venv
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install west

# West init
if [ ! -f ".west/config" ]; then
    echo -e "${BLUE}Initializing west workspace...${NC}"
    west init -m https://github.com/zephyrproject-rtos/zephyr --mr "$ZEPHYR_REV"
    print_success "West workspace initialized"
else
    print_success "West workspace already initialized"
fi

echo -e "${BLUE}Updating repositories...${NC}"
west update --narrow 

pip install -r zephyr/scripts/requirements.txt
pip install -r bootloader/mcuboot/scripts/requirements.txt

# Zephyr SDK
if [ ! -d ~/.local/zephyr-sdk ] && [ ! -d /opt/zephyr-sdk ]; then
    echo -e "${BLUE}Installing Zephyr SDK...${NC}"
    west sdk install
    print_success "Zephyr SDK installed"
else
    print_success "Zephyr SDK already installed"
fi

west zephyr-export
print_success "Zephyr environment ready"

# ----------------------------- MCUboot Build -----------------------------
echo -e "${BLUE}Building MCUboot (RSA-2048 + USB CDC-ACM DFU)...${NC}"

if [ -d "$MCU_BOOT_BUILD_DIR" ]; then
    print_warning "MCUboot build directory already exists."
    read -t 15 -p "Rebuild from scratch? (y/N): " -n 1 -r || true
    echo
    if [[ ${REPLY:-} =~ ^[Yy]$ ]]; then
        rm -rf "$MCU_BOOT_BUILD_DIR"
        print_warning "Old build removed"
    else
        print_warning "Skipping rebuild"
        goto_final
    fi
fi

west build -b nrf52840dongle/nrf52840/bare \
    bootloader/mcuboot/boot/zephyr \
    -d "$MCU_BOOT_BUILD_DIR" \
    --force \
    -- \
    -DCONFIG_BOOT_SIGNATURE_TYPE_RSA=y \
    -DCONFIG_BOOT_SIGNATURE_TYPE_RSA_LEN=2048 \
    -DCONFIG_BOOT_IMG_HASH_ALG_SHA256=y \
    -DCONFIG_BOOT_ERASE_PROGRESSIVELY=y \
    -DCONFIG_BOOT_SWAP_USING_MOVE=y \
    -DCONFIG_BOOT_MAX_IMG_SECTORS=256 \
    -DOVERLAY_CONFIG=usb_cdc_acm_recovery.conf

print_success "MCUboot built successfully!"

# ----------------------------- OpenOCD Setup -----------------------------
echo -e "${BLUE}Building and installing latest OpenOCD for Raspberry Pi 5...${NC}"

cd ~
if [ -d "openocd" ]; then
    echo "Updating OpenOCD..."
    cd openocd && git pull --recurse-submodules
else
    git clone --recursive https://github.com/openocd-org/openocd.git openocd
    cd openocd
fi

./bootstrap
./configure --enable-linuxgpiod --enable-ftdi --enable-cmsis-dap \
            --enable-internal-jimtcl --disable-werror

make -j$(nproc)
sudo make install

# Pi 5 SWD config
cat > ~/pi5-nrf52840-swd.cfg << 'EOF'
adapter driver linuxgpiod
adapter gpio swdio 24 -chip 0
adapter gpio swclk 25 -chip 0
transport select swd
adapter speed 1000
telnet_port 4444
gdb_port 3333
echo "Pi 5 SWD ready (gpiochip0)"
EOF

print_success "OpenOCD installed"

# Helper scripts
cat > ~/start-openocd.sh << 'START'
#!/usr/bin/env bash
sudo pkill openocd 2>/dev/null || true
sleep 1
sudo openocd -s /usr/local/share/openocd/scripts \
  -f ~/pi5-nrf52840-swd.cfg -f target/nordic/nrf52.cfg -c "init" > ~/openocd.log 2>&1 &
echo "OpenOCD started. Log: tail -f ~/openocd.log"
START

cat > ~/stop-openocd.sh << 'STOP'
#!/usr/bin/env bash
sudo pkill openocd && echo "OpenOCD stopped" || echo "OpenOCD not running"
STOP

cat > ~/flash-mcuboot.sh << 'FLASH'
#!/usr/bin/env bash
if [ ! -f ~/zephyrproject/build/mcuboot_bare/zephyr/zephyr.hex ]; then
    echo "Error: MCUboot hex not found!"
    exit 1
fi
sudo openocd -s /usr/local/share/openocd/scripts \
  -f ~/pi5-nrf52840-swd.cfg -f target/nordic/nrf52.cfg \
  -c "init" -c "reset init" \
  -c "program ~/zephyrproject/build/mcuboot_bare/zephyr/zephyr.hex verify" \
  -c "reset run" -c "shutdown"
echo "MCUboot flashed."
FLASH

chmod +x ~/start-openocd.sh ~/stop-openocd.sh ~/flash-mcuboot.sh

# ----------------------------- Final Summary -----------------------------
goto_final() {
    echo ""
    echo -e "${GREEN}=== SETUP COMPLETED SUCCESSFULLY! ===${NC}"
    echo ""
    echo "To activate the environment:"
    echo -e "   ${BLUE}source $INSTALL_DIR/.venv/bin/activate${NC}"
    echo ""
    echo "Test OpenOCD:"
    echo "   ~/start-openocd.sh"
    echo "   telnet localhost 4444"
    echo ""
    echo "Flash MCUboot:"
    echo "   ~/flash-mcuboot.sh"
    echo ""
    echo -e "${YELLOW}Tip:${NC} Reboot recommended after group changes for full GPIO access."
    echo "You can now re-run this script anytime with minimal prompts."
    exit 0
}

goto_final 
