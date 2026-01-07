<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Setting Up Zephyr RTOS Development Environment and Building/Flashing the Blinky Sample for Nordic nRF52840 Dongle</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; line-height: 1.6; color: #333; background: #fff; padding: 20px; }
        h1, h2 { text-align: center; color: #2c3e50; }
        h2 { margin-top: 40px; }
        p { text-align: justify; }
        ul { margin-left: 40px; }
        figure { text-align: center; margin: 30px 0; }
        figcaption { font-style: italic; margin-top: 10px; color: #555; }
        img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; }
        .page-break { page-break-after: always; }
        footer { text-align: center; margin-top: 50px; font-size: 0.9em; color: #777; }
    </style>
</head>
<body>

    <h1>Setting Up Zephyr RTOS Development Environment<br>and Building/Flashing the Blinky Sample<br>for Nordic nRF52840 Dongle</h1>
    <p style="text-align:center;"><em>January 2026</em></p>

    <h2>1 Overview</h2>
    <p>This guide describes the process of setting up a Zephyr RTOS development environment on a Raspberry Pi (Debian Bookworm), building MCUboot as the primary bootloader for USB DFU support, building the basic “blinky” LED sample for the Nordic Semiconductor nRF52840 Dongle (bare configuration), signing the image, and flashing/programming via SWD using OpenOCD with Raspberry Pi GPIO pins or updating via MCUboot USB serial recovery.</p>
    <p>This example requires no special equipment, no hardware edits, all hardware available online, and no soldering.</p>
    <p>The nRF52840 Dongle is a compact USB dongle featuring the nRF52840 SoC, commonly used for Bluetooth Low Energy and other wireless applications in Zephyr projects. Using MCUboot replaces the native Nordic bootloader and enables secure firmware updates over USB.</p>

    <figure>
        <img src="https://infocenter.nordicsemi.com/topic/struct_nrf52/struct/nrf52840_dongle.png" alt="Official Nordic nRF52840 Dongle">
        <figcaption>Figure 1: Official Nordic nRF52840 Dongle</figcaption>
    </figure>

    <h2>2 Hardware Connections for SWD Flashing</h2>
    <p>To flash the dongle using OpenOCD on Raspberry Pi GPIO, connect the following pins:</p>
    <ul>
        <li>Raspberry Pi GPIO 24 (SWDIO) → Dongle SWDIO</li>
        <li>Raspberry Pi GPIO 25 (SWCLK) → Dongle SWCLK</li>
        <li>Raspberry Pi GND → Dongle GND</li>
        <li>(Optional) Raspberry Pi 3.3V → Dongle VCC if not powered via USB</li>
    </ul>

    <footer>
        Page 1 of 4<br>
        © 2026 – Zephyr on Raspberry Pi Project
    </footer>

</body>
</html>
