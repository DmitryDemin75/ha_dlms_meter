"""Constants for DLMS integration."""
from __future__ import annotations

from typing import Final
from homeassistant.const import Platform, CONF_NAME, CONF_SCAN_INTERVAL

# The domain of your component. Should be equal to the name of your component.
DOMAIN: Final = "dlms"

# Configuration parameters
CONF_SERIAL_PORT: Final = "serial_port"
CONF_DEVICE: Final = "device"
CONF_QUERY_CODE: Final = "query_code"
CONF_BAUDRATE: Final = "baudrate"
CONF_BYTESIZE: Final = "bytesize"
CONF_PARITY: Final = "parity"
CONF_STOPBITS: Final = "stopbits"
CONF_TIMEOUT: Final = "timeout"
CONF_ONLY_LISTEN: Final = "only_listen"
CONF_USE_CHECKSUM: Final = "use_checksum"
CONF_UPDATE_INTERVAL: Final = "update_interval"

# Default values
DEFAULT_SERIAL_PORT: Final = "/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0"
DEFAULT_DEVICE: Final = ""
DEFAULT_QUERY_CODE: Final = "?"
DEFAULT_BAUDRATE: Final = 300  # Начальная скорость 300 бод
DEFAULT_BYTESIZE: Final = 7
DEFAULT_PARITY: Final = "E"
DEFAULT_STOPBITS: Final = 1
DEFAULT_TIMEOUT: Final = 3  # 3 секунды как в тестовом скрипте
DEFAULT_ONLY_LISTEN: Final = False
DEFAULT_USE_CHECKSUM: Final = True
DEFAULT_UPDATE_INTERVAL: Final = 3600  # 1 час в секундах

# OBIS codes for different measurements
OBIS_CODES = {
    "1.0.0.1.0.255": {
        "name": "Active Energy Import",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "1.0.0.2.0.255": {
        "name": "Active Energy Export",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
    },
    "1.0.0.3.0.255": {
        "name": "Reactive Energy Import",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kvarh",
    },
    "1.0.0.4.0.255": {
        "name": "Reactive Energy Export",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kvarh",
    },
    "1.0.0.5.0.255": {
        "name": "Active Power Import",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
    },
    "1.0.0.6.0.255": {
        "name": "Active Power Export",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
    },
    "1.0.0.7.0.255": {
        "name": "Reactive Power Import",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "var",
    },
    "1.0.0.8.0.255": {
        "name": "Reactive Power Export",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "var",
    },
    "1.0.0.9.0.255": {
        "name": "Current L1",
        "device_class": "current",
        "state_class": "measurement",
        "unit": "A",
    },
    "1.0.0.10.0.255": {
        "name": "Current L2",
        "device_class": "current",
        "state_class": "measurement",
        "unit": "A",
    },
    "1.0.0.11.0.255": {
        "name": "Current L3",
        "device_class": "current",
        "state_class": "measurement",
        "unit": "A",
    },
    "1.0.0.12.0.255": {
        "name": "Voltage L1",
        "device_class": "voltage",
        "state_class": "measurement",
        "unit": "V",
    },
    "1.0.0.13.0.255": {
        "name": "Voltage L2",
        "device_class": "voltage",
        "state_class": "measurement",
        "unit": "V",
    },
    "1.0.0.14.0.255": {
        "name": "Voltage L3",
        "device_class": "voltage",
        "state_class": "measurement",
        "unit": "V",
    },
    "1.0.0.15.0.255": {
        "name": "Power Factor",
        "device_class": "power_factor",
        "state_class": "measurement",
        "unit": None,
    },
    "1.0.0.16.0.255": {
        "name": "Frequency",
        "device_class": "frequency",
        "state_class": "measurement",
        "unit": "Hz",
    },
}

PLATFORMS: Final = [Platform.SENSOR]

# Настройки логирования
DEFAULT_LOG_LEVEL: Final = "INFO"  # Изменено с DEBUG на INFO
