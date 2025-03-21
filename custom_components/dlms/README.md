# DLMS Integration for Home Assistant

This integration allows you to connect electricity meters supporting the DLMS protocol to Home Assistant
and receive electricity consumption data.

## Installation

### Manual Installation
1. Copy the `dlms` directory to the `custom_components` directory of your Home Assistant.
2. Restart Home Assistant.
3. Add the integration through "Settings" > "Devices & Services" > "Add Integration" > "DLMS".

### HACS Installation
1. Make sure you have [HACS](https://hacs.xyz/) installed in your Home Assistant instance.
2. Click on the button below to add this repository to HACS:
   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=DmitryDemin75&repository=ha_dlms_meter&category=integration)
3. Install the integration from HACS.
4. Restart Home Assistant.
5. Add the integration through "Settings" > "Devices & Services" > "Add Integration" > "DLMS".

## Compatibility and Limitations

This integration has been tested with the following setup:
- Meter model: Landis+Gyr E650
- Electricity provider: EAC (Electricity Authority of Cyprus)
- Connection method: Optical port

**Important limitations:**
- Compatibility with other electricity meters is not guaranteed
- The integration uses a simple connection method and does not use DLMS passwords for extended functionality
- EAC does not share advanced access credentials but allows reading basic data in open mode
- Data on the meter is only updated on the 1st day of each month

Despite these limitations, the integration is still useful for understanding energy consumption or grid export volumes, which is particularly valuable for homes with solar generation systems.

## Usage and Modification

This code is freely available for anyone to use and modify according to their needs. Feel free to adapt it to work with different meter models or utility providers, or to extend its functionality as required for your specific setup.

## Available Services

### set_log_level

Sets the logging level for debugging the integration.

**Parameters:**
- `level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

**Example:**
```yaml
service: dlms.set_log_level
data:
  level: DEBUG
```

### run_test

Performs a connection test with the device and displays results as a notification and creates a sensor `sensor.dlms_test_result`.

**Parameters:**
- `serial_port`: Device port path (required)
- `device`: Device identifier (optional)
- `query_code`: Query code (optional)
- `baudrate`: Port speed in baud (optional)

**Example:**
```yaml
service: dlms.run_test
data:
  serial_port: /dev/ttyUSB0
  device: "01"
  query_code: "?"
  baudrate: 300
```

### run_raw_test

Performs a connection test and returns raw data as a notification and creates a sensor `sensor.dlms_raw_test_result`.

**Parameters:**
- `serial_port`: Device port path (required)
- `device`: Device identifier (optional)
- `query_code`: Query code (optional)
- `baudrate`: Port speed in baud (optional)

**Example:**
```yaml
service: dlms.run_raw_test
data:
  serial_port: /dev/ttyUSB0
  device: "01"
  query_code: "?"
  baudrate: 300
```

### force_update

Performs an unscheduled data update for an existing integration.

**Parameters:**
- No parameters, automatically updates the DLMS integration data

**Example:**
```yaml
service: dlms.force_update
```

## Viewing Test Results

After calling the `run_test` or `run_raw_test` services, the results will be displayed:

1. In Home Assistant notifications (bell icon in the upper right corner)
2. As sensors `sensor.dlms_test_result` and `sensor.dlms_raw_test_result`

These sensors can be added to the dashboard for easy access to test results.

## Automations

You can create an automation for regular testing and tracking of results:

```yaml
automation:
  - alias: "Daily DLMS Test"
    trigger:
      - platform: time
        at: "03:00:00"
    action:
      - service: dlms.run_test
        data:
          serial_port: /dev/ttyUSB0
```

## Troubleshooting

If the integration is not working properly:

1. Set the logging level to DEBUG: `service: dlms.set_log_level, data: { level: DEBUG }`
2. Check the logs: Settings > System > Logs
3. Run a test using `dlms.run_raw_test` to see the raw data
4. Make sure the device is connected to the correct port and has the correct settings 