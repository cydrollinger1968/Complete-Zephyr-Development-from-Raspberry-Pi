#!/bin/bash
set -e

echo "=== Zephyr + MCUboot + USB DFU Setup for nRF52840 Dongle on Raspberry Pi Bookworm ==="

# Update and install system packages (added git for mcumgr clone if needed)
apt update
apt install -y git cmake ninja-build gperf python3 python3-venv python3-pip libusb-1.0-0 ccache openocd gdb-multiarch wget xz-utils

# Create dev user
if ! id -u dev >/dev/null 2>&1; then
    adduser --disabled-password --gecos "" dev
    echo "dev ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/010_dev-nopasswd
    chmod 0440 /etc/sudoers.d/010_dev-nopasswd
fi
usermod -aG dialout dev

# Run as dev user
su - dev -c "
set -e

cd ~

# Bashrc helpers
echo 'cd ~/zephyrproject && [ -f .venv/bin/activate ] && source .venv/bin/activate' >> .bashrc
echo 'export PATH=\"/usr/lib/ccache:\$PATH\"' >> .bashrc
echo 'export ZEPHYR_SDK_INSTALL_DIR=~/zephyr-sdk-0.17.4' >> .bashrc

# Install Go (latest stable for mcumgr)
if ! command -v go &> /dev/null; then
    wget https://go.dev/dl/go1.23.5.linux-arm64.tar.gz
    sudo tar -C /usr/local -xzf go1.23.5.linux-arm64.tar.gz
    rm go1.23.5.linux-arm64.tar.gz
    echo 'export PATH=\$PATH:/usr/local/go/bin:\$HOME/go/bin' >> ~/.bashrc
    echo 'export GOPATH=\$HOME/go' >> ~/.bashrc
fi

# Zephyr workspace
if [ ! -d zephyrproject ]; then
    python3 -m venv zephyrproject/.venv
    source zephyrproject/.venv/bin/activate
    pip install --break-system-packages west imgtool
    west init zephyrproject
    cd zephyrproject
    west update
    west zephyr-export
    pip install --break-system-packages -r zephyr/scripts/requirements.txt
    pip install --break-system-packages -r zephyr/scripts/requirements-base.txt
else
    cd zephyrproject
    [ -f .venv/bin/activate ] && source .venv/bin/activate
fi

# Zephyr SDK
if [ ! -d zephyr-sdk-0.17.4 ]; then
    cd ~
    wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.17.4/zephyr-sdk-0.17.4_linux-aarch64.tar.xz
    tar xvf zephyr-sdk-0.17.4_linux-aarch64.tar.xz
    cd zephyr-sdk-0.17.4
    ./setup.sh -t all <<EOF
y
EOF
fi

# OpenOCD config
cat > ~/openocd.cfg << 'OCD'
adapter driver bcm2835gpio

bcm2835gpio peripheral_base 0xFE000000
bcm2835gpio speed_coeffs 236181 60

adapter gpio swdio 24
adapter gpio swclk 25

transport select swd
source [find target/nordic/nrf52.cfg]

adapter speed 1000
OCD

# MCUboot config
cd ~/zephyrproject  # Ensure in correct dir
mkdir -p bootloader/mcuboot/boot/zephyr
cat > bootloader/mcuboot/boot/zephyr/mcuboot_serial.conf << 'MCUBOOT'
CONFIG_MCUBOOT_SERIAL=y
CONFIG_BOOT_SERIAL_CDC_ACM=y
CONFIG_USB_DEVICE_STACK=y
CONFIG_USB_DEVICE_PID=0x1001
CONFIG_USB_DEVICE_PRODUCT="MCUboot"
CONFIG_MCUBOOT_INDICATION_LED=y
CONFIG_WARN_DEPRECATED=n  # Suppress USB deprecation warnings
CONFIG_MCUBOOT_LOG_LEVEL_OFF=y  # Disable logging to fix choice warnings
MCUBOOT

# Signing key (fixed command)
[ -f .venv/bin/activate ] && source .venv/bin/activate
if [ ! -f bootloader/mcuboot/root-rsa-2048.pem ]; then
    imgtool keygen -k bootloader/mcuboot/root-rsa-2048.pem -t rsa-2048
fi

# Install mcumgr CLI (latest from official repo)
export PATH=\$PATH:/usr/local/go/bin:\$HOME/go/bin
export GOPATH=\$HOME/go
go install github.com/apache/mynewt-mcumgr-cli/mcumgr@latest

# Build MCUboot
west build -p always -b nrf52840dongle/nrf52840/bare -d build-mcuboot bootloader/mcuboot/boot/zephyr DEXTRA_CONF_FILE=bootloader/mcuboot/boot/zephyr/mcuboot_serial.conf

# Flash MCUboot via SWD (requires hardware connected)
echo '=== Flashing MCUboot via OpenOCD (ensure SWD is connected) ==='
sudo openocd -f ~/openocd.cfg -c 'init; reset halt; nrf5 mass_erase; program build-mcuboot/zephyr/zephyr.hex verify; reset; exit'

# Build Blinky for MCUboot
west build -p always -b nrf52840dongle/nrf52840/bare -d build/blinky zephyr/samples/basic/blinky -- -DCONFIG_BOOTLOADER_MCUBOOT=y

# Sign Blinky
west sign -d build/blinky -t imgtool -- --key bootloader/mcuboot/root-rsa-2048.pem

# Instructions for mcumgr upload (manual recovery mode entry)
echo '=== MCUboot and Blinky built/signed! To upload: ==='
echo '1. Unplug dongle, hold button (SW1), plug in (enter recovery mode: /dev/ttyACM0 appears).'
echo '2. Run: mcumgr --conntype=serial --connstring=\"dev=/dev/ttyACM0,baud=115200\" image upload -e build/blinky/zephyr/zephyr.signed.bin'
echo '3. mcumgr --conntype=serial --connstring=\"dev=/dev/ttyACM0,baud=115200\" image list'
echo '4. mcumgr --conntype=serial --connstring=\"dev=/dev/ttyACM0,baud=115200\" image confirm'
echo '5. mcumgr --conntype=serial --connstring=\"dev=/dev/ttyACM0,baud=115200\" reset'
echo 'The RGB LED should now blink!'
"

echo "=== SETUP COMPLETE! ==="
echo "Run: sudo reboot"
echo "After reboot, log in as 'dev' — your Zephyr environment is ready (including mcumgr)."
echo "MCUboot and Blinky have been built and flashed (MCUboot via SWD); follow instructions for final USB upload."