# Home Assistant DLMS Meter Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

This integration allows you to connect electricity meters supporting the DLMS protocol to Home Assistant
and receive electricity consumption data.

**This integration is tested with Landis+Gyr E650 meter used by EAC (Electricity Authority of Cyprus).**

![DLMS Integration][exampleimg]

## Installation

### HACS Installation

1. Make sure you have [HACS](https://hacs.xyz/) installed in your Home Assistant instance.
2. Add this repository to your HACS by clicking on the button below:
   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=DmitryDemin75&repository=ha_dlms_meter&category=integration)
3. Install the integration from HACS.
4. Restart Home Assistant.
5. Add the integration through "Settings" > "Devices & Services" > "Add Integration" > "DLMS".

### Manual Installation

1. Copy the `custom_components/dlms` directory to the `custom_components` directory of your Home Assistant.
2. Restart Home Assistant.
3. Add the integration through "Settings" > "Devices & Services" > "Add Integration" > "DLMS".

## Configuration

After installation, follow the configuration flow in the Home Assistant UI.

## Compatibility and Limitations

For detailed information on compatibility, limitations, services, and troubleshooting, please see the [integration's documentation](custom_components/dlms/README.md).

## Usage and Modification

This code is freely available for anyone to use and modify according to their needs. Feel free to adapt it to work with different meter models or utility providers, or to extend its functionality as required for your specific setup.

## Contributing

If you want to contribute to this integration, please read the [Contribution guidelines](CONTRIBUTING.md)

***

[integration]: https://github.com/DmitryDemin75/ha_dlms_meter
[exampleimg]: https://raw.githubusercontent.com/DmitryDemin75/ha_dlms_meter/main/example.png
[commits-shield]: https://img.shields.io/github/commit-activity/y/DmitryDemin75/ha_dlms_meter.svg
[commits]: https://github.com/DmitryDemin75/ha_dlms_meter/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[license]: https://github.com/DmitryDemin75/ha_dlms_meter/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/DmitryDemin75/ha_dlms_meter.svg
[maintenance-shield]: https://img.shields.io/badge/maintainer-DmitryDemin75-blue.svg
[releases-shield]: https://img.shields.io/github/release/DmitryDemin75/ha_dlms_meter.svg
[releases]: https://github.com/DmitryDemin75/ha_dlms_meter/releases
[user_profile]: https://github.com/DmitryDemin75 