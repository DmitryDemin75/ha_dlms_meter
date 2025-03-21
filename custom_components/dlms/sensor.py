"""Support for DLMS sensors."""

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .dlms import DLMSDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# OBIS коды для различных измерений
OBIS_CODES = {
    "1.8.0": {
        "name": "1.8.0",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "2.8.0": {
        "name": "2.8.0",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "9.2.0": {
        "name": "9.2.0",
        "unit": "kVA",
        "device_class": None,
        "state_class": "measurement",
    },
    "9.6.0": {
        "name": "9.6.0",
        "unit": "kVA",
        "device_class": None,
        "state_class": "measurement",
    },
    "132.8.0": {
        "name": "132.8.0",
        "unit": "kvarh",
        "device_class": None,
        "state_class": "total_increasing",
    },
    "9.8.0": {
        "name": "9.8.0",
        "unit": "kVAh",
        "device_class": None,
        "state_class": "total_increasing",
    },
    "0.1.0": {
        "name": "0.1.0",
        "unit": None,
        "device_class": "power_factor",
        "state_class": "measurement",
    },
    "1.8.1": {
        "name": "1.8.1",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "1.8.2": {
        "name": "1.8.2",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "1.8.3": {
        "name": "1.8.3",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "1.8.4": {
        "name": "1.8.4",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "1.8.5": {
        "name": "1.8.5",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "1.8.6": {
        "name": "1.8.6",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "1.8.7": {
        "name": "1.8.7",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "1.8.8": {
        "name": "1.8.8",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up DLMS sensor based on config_entry."""
    _LOGGER.info("Setting up DLMS sensors")
    
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if not coordinator:
        _LOGGER.error("No coordinator found for entry_id: %s", entry.entry_id)
        return

    # Создаём сенсоры сразу, без ожидания данных
    sensors = [
        DLMSSensor(coordinator, obis_code, config)
        for obis_code, config in OBIS_CODES.items()
    ]
    
    _LOGGER.info("Adding %d DLMS sensors", len(sensors))
    async_add_entities(sensors, True)
    _LOGGER.info("DLMS sensors setup completed")

class DLMSBaseSensor(SensorEntity):
    """Base class for DLMS sensors."""

    def __init__(
        self,
        coordinator: DLMSDataUpdateCoordinator,
        name: str,
        obis_code: str,
        unit_of_measurement: str | None = None,
        device_class: str | None = None,
        state_class: str | None = None,
        icon: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._attr_name = name
        self._obis_code = obis_code
        # Генерируем entity_id в формате dlms_1_8_0
        formatted_code = obis_code.replace(".", "_")
        self.entity_id = f"sensor.dlms_{formatted_code}"
        self._attr_unique_id = f"dlms_{formatted_code}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.dlms_data.serial_port)},
            "name": f"DLMS Meter ({coordinator.dlms_data.serial_port})",
            "manufacturer": "LGZ",
            "model": "LGZ5",
        }
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        data = self.coordinator.data.get(self._obis_code)
        if not data:
            return None
        return data.get("value")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if not self.coordinator.data:
            return None
            
        attrs = {}
        
        # Проверяем, есть ли данные для конкретного OBIS кода
        obis_data = self.coordinator.data.get(self._obis_code)
        if obis_data:
            # Проверяем, есть ли индивидуальные данные о дате и времени для этого кода
            if 'date' in obis_data:
                attrs['measurement_date'] = obis_data['date']
            if 'time' in obis_data:
                attrs['measurement_time'] = obis_data['time']
        
        # Если для этого кода нет своих данных о дате и времени,
        # используем общие данные (если они есть)
        if 'measurement_date' not in attrs and '_date' in self.coordinator.data:
            attrs['measurement_date'] = self.coordinator.data['_date']
        if 'measurement_time' not in attrs and '_time' in self.coordinator.data:
            attrs['measurement_time'] = self.coordinator.data['_time']
            
        return attrs

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._attr_unique_id

class DLMSSensor(DLMSBaseSensor):
    """Representation of a DLMS sensor."""

    def __init__(
        self,
        coordinator: DLMSDataUpdateCoordinator,
        obis_code: str,
        config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config.get("name", f"DLMS {obis_code}"), obis_code, config.get("unit"), config.get("device_class"), config.get("state_class"))
        self._attr_should_poll = False
        self._attr_available = False

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        ) 