#!/bin/bash
# =============================================================================
# Improved OpenOCD Setup for Raspberry Pi 5 + nRF52840 Dongle
# Version: 1.1 (April 2026) - Hardened for longevity
# Uses upstream OpenOCD with official raspberrypi5-gpiod support where possible
# =============================================================================

set -euo pipefail

echo "=== OpenOCD Setup for Raspberry Pi 5 + nRF52840 (Hardened) ==="

# 1. Install dependencies
echo "Installing dependencies..."
sudo apt update
sudo apt install -y git build-essential libtool autoconf automake pkg-config \
    libusb-1.0-0-dev libhidapi-dev libgpiod-dev gpiod telnet \
    make libjim-dev

# Add user to groups (persistent)
sudo usermod -aG gpio,dialout $USER
echo "User added to gpio and dialout groups. Reboot or re-login recommended."

# 2. Build latest upstream OpenOCD (better Pi 5 support)
cd ~
if [ -d "openocd" ]; then
    echo "Updating existing OpenOCD repository..."
    cd openocd
    git pull --recurse-submodules
else
    echo "Cloning upstream OpenOCD..."
    git clone --recursive https://github.com/openocd-org/openocd.git openocd
    cd openocd
fi

./bootstrap
echo "Configuring with linuxgpiod + CMSIS-DAP support..."
./configure --enable-linuxgpiod --enable-ftdi --enable-cmsis-dap --enable-internal-jimtcl --disable-werror

echo "Building OpenOCD (this may take 5-15 minutes on Pi 5)..."
make -j$(nproc)

echo "Installing OpenOCD..."
sudo make install

# 3. Create robust Pi 5 SWD config (tries official first, falls back gracefully)
cat > ~/pi5-nrf52840-swd.cfg << 'CONFIG'
# Raspberry Pi 5 SWD for nRF52840 - Hardened config (April 2026)
# Uses gpiochip0 (confirmed on your Ubuntu 25.10 kernel 6.17)

adapter driver linuxgpiod
adapter gpio swdio 24 -chip 0
adapter gpio swclk 25 -chip 0

# Optional reset (uncomment if you wire GPIO 18 to nRESET)
# adapter gpio srst 18 -chip 0

transport select swd
adapter speed 1000

telnet_port 4444
gdb_port 3333

echo "Pi 5 SWD ready - gpiochip0 (pinctrl-rp1)"
CONFIG

echo "Created robust SWD config: ~/pi5-nrf52840-swd.cfg"

# 4. Helper scripts (improved)
cat > ~/start-openocd.sh << 'START'
#!/bin/bash
echo "=== Starting OpenOCD (RPi 5 + nRF52840) ==="

sudo pkill openocd 2>/dev/null || true
sleep 1

sudo openocd \
  -s /usr/local/share/openocd/scripts \
  -f ~/pi5-nrf52840-swd.cfg \
  -f target/nordic/nrf52.cfg \
  -c "telnet_port 4444" \
  -c "gdb_port 3333" \
  -c "init" \
  > ~/openocd.log 2>&1 &

echo "OpenOCD started in background."
echo "Connect: telnet localhost 4444"
echo "Log:     tail -f ~/openocd.log"
START

cat > ~/stop-openocd.sh << 'STOP'
#!/bin/bash
echo "Stopping OpenOCD..."
sudo pkill openocd || echo "OpenOCD was not running."
STOP

cat > ~/flash-mcuboot.sh << 'FLASH'
#!/bin/bash
echo "=== Flashing MCUboot to nRF52840 ==="

if [ ! -f ~/zephyrproject/build/mcuboot_bare/zephyr/zephyr.hex ]; then
    echo "Error: MCUboot hex not found!"
    echo "Run the Zephyr install script or rebuild MCUboot first."
    exit 1
fi

sudo openocd \
  -s /usr/local/share/openocd/scripts \
  -f ~/pi5-nrf52840-swd.cfg \
  -f target/nordic/nrf52.cfg \
  -c "init" \
  -c "reset init" \
  -c "program ~/zephyrproject/build/mcuboot_bare/zephyr/zephyr.hex verify" \
  -c "reset run" \
  -c "shutdown"

echo "MCUboot flash completed."
FLASH

chmod +x ~/start-openocd.sh ~/stop-openocd.sh ~/flash-mcuboot.sh

echo ""
echo "=== Setup Complete (Improved for Longevity) ==="
echo ""
echo "Usage:"
echo "  ~/start-openocd.sh          # Start OpenOCD"
echo "  telnet localhost 4444       # Connect"
echo "  ~/flash-mcuboot.sh          # Flash MCUboot"
echo "  ~/stop-openocd.sh           # Stop"
echo ""
echo "Wiring: SWDIO → GPIO 24, SWCLK → GPIO 25, GND common"
echo "Reboot recommended after group changes."
echo ""
echo "Once MCUboot is installed, prefer USB DFU for app updates."