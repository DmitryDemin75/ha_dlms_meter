"""The DLMS integration."""

import logging
from datetime import timedelta
from typing import Any
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_SERIAL_PORT,
    CONF_DEVICE,
    CONF_QUERY_CODE,
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_PARITY,
    CONF_STOPBITS,
    CONF_TIMEOUT,
    CONF_ONLY_LISTEN,
    CONF_USE_CHECKSUM,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_STOPBITS,
    DEFAULT_TIMEOUT,
    DEFAULT_ONLY_LISTEN,
    DEFAULT_USE_CHECKSUM,
    DEFAULT_DEVICE,
    DEFAULT_QUERY_CODE,
    DEFAULT_SERIAL_PORT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    Platform
)
from .dlms import DLMSData, DLMSDataUpdateCoordinator
from .config_flow import DLMSConfigFlow
from homeassistant.components import persistent_notification
from homeassistant.helpers.entity_platform import async_get_platforms

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

TEST_DLMS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERIAL_PORT, default=DEFAULT_SERIAL_PORT): cv.string,
        vol.Optional(CONF_DEVICE, default=DEFAULT_DEVICE): cv.string,
        vol.Optional(CONF_QUERY_CODE, default=DEFAULT_QUERY_CODE): cv.string,
        vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): cv.positive_int,
        vol.Optional(CONF_BYTESIZE, default=DEFAULT_BYTESIZE): cv.positive_int,
        vol.Optional(CONF_PARITY, default=DEFAULT_PARITY): cv.string,
        vol.Optional(CONF_STOPBITS, default=DEFAULT_STOPBITS): cv.positive_int,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_ONLY_LISTEN, default=DEFAULT_ONLY_LISTEN): cv.boolean,
        vol.Optional(CONF_USE_CHECKSUM, default=DEFAULT_USE_CHECKSUM): cv.boolean,
    }
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the DLMS integration."""
    _LOGGER.info("Setting up DLMS integration")

    # Регистрируем сервис для настройки уровня логирования
    async def set_log_level(call: ServiceCall) -> None:
        """Set the log level for DLMS integration."""
        level = call.data.get("level", "INFO")
        logging.getLogger("custom_components.dlms").setLevel(level)
        _LOGGER.info("DLMS log level set to %s", level)

    hass.services.async_register(DOMAIN, "set_log_level", set_log_level)
    _LOGGER.info("Registering DLMS service")

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DLMS from a config entry."""
    _LOGGER.info("Setting up DLMS integration")

    # Регистрируем сервис для запуска теста
    async def async_run_dlms_test(call: ServiceCall) -> None:
        """Run DLMS test."""
        _LOGGER.info("Running DLMS test")
        port = call.data.get(CONF_SERIAL_PORT, DEFAULT_SERIAL_PORT)
        
        # Создаем объект DLMSData с настройками из вызова сервиса
        dlms_data = DLMSData(
            serial_port=port,
            device=call.data.get(CONF_DEVICE, DEFAULT_DEVICE),
            query_code=call.data.get(CONF_QUERY_CODE, DEFAULT_QUERY_CODE),
            baud_rate=call.data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE),
            bytesize=call.data.get(CONF_BYTESIZE, DEFAULT_BYTESIZE),
            parity=call.data.get(CONF_PARITY, DEFAULT_PARITY),
            stopbits=call.data.get(CONF_STOPBITS, DEFAULT_STOPBITS),
            timeout=call.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            only_listen=call.data.get(CONF_ONLY_LISTEN, DEFAULT_ONLY_LISTEN),
            use_checksum=call.data.get(CONF_USE_CHECKSUM, DEFAULT_USE_CHECKSUM),
        )
        
        _LOGGER.info("Starting DLMS test with port: %s", port)
        
        # Запускаем чтение данных
        result = await dlms_data.read_data()
        
        # Формируем результат в удобном для чтения формате
        if result:
            _LOGGER.info("DLMS test successful! Received data:")
            message = "DLMS тест выполнен успешно!\nПолученные данные:\n\n"
            for obis_code, data in result.items():
                if isinstance(data, dict):
                    data_str = f"значение: {data.get('value', 'н/д')}"
                    if 'unit' in data and data['unit']:
                        data_str += f", единица: {data['unit']}"
                    if 'date' in data and data['date']:
                        data_str += f", дата: {data['date']}"
                    if 'time' in data and data['time']:
                        data_str += f", время: {data['time']}"
                else:
                    data_str = str(data)
                
                message += f"{obis_code}: {data_str}\n"
                _LOGGER.info("  %s: %s", obis_code, data)
                
            # Создаем уведомление с результатами
            persistent_notification.async_create(
                hass,
                message,
                title="Результаты DLMS теста",
                notification_id="dlms_test_result"
            )
            
            # Обновляем датчик с результатами
            hass.states.async_set(
                "sensor.dlms_test_result", 
                "success", 
                {"parsed_data": result, 
                 "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "message": message}
            )
            
        else:
            _LOGGER.warning("DLMS test failed! No data received.")
            message = "DLMS тест не удался! Данные не получены."
            
            # Создаем уведомление с результатами
            persistent_notification.async_create(
                hass,
                message,
                title="Результаты DLMS теста",
                notification_id="dlms_test_result"
            )
            
            # Обновляем датчик с результатами
            hass.states.async_set(
                "sensor.dlms_test_result", 
                "failed", 
                {"last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "message": message}
            )
        
        # Закрываем соединение
        dlms_data.disconnect()

    async def run_raw_test(call: ServiceCall) -> None:
        """Запуск теста DLMS с возвратом необработанных данных."""
        _LOGGER.info("Running DLMS raw test")
        port = call.data.get(CONF_SERIAL_PORT, DEFAULT_SERIAL_PORT)
        
        # Создаем объект DLMSData с настройками из вызова сервиса
        dlms_data = DLMSData(
            serial_port=port,
            device=call.data.get(CONF_DEVICE, DEFAULT_DEVICE),
            query_code=call.data.get(CONF_QUERY_CODE, DEFAULT_QUERY_CODE),
            baud_rate=call.data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE),
            bytesize=call.data.get(CONF_BYTESIZE, DEFAULT_BYTESIZE),
            parity=call.data.get(CONF_PARITY, DEFAULT_PARITY),
            stopbits=call.data.get(CONF_STOPBITS, DEFAULT_STOPBITS),
            timeout=call.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            only_listen=call.data.get(CONF_ONLY_LISTEN, DEFAULT_ONLY_LISTEN),
            use_checksum=call.data.get(CONF_USE_CHECKSUM, DEFAULT_USE_CHECKSUM),
        )
        
        _LOGGER.info("Starting DLMS raw test with port: %s", port)
        
        # Запускаем тест с получением необработанных данных
        raw_data = await dlms_data.run_test()
        
        # Отправляем результат как event
        hass.bus.async_fire("dlms_raw_test_result", {"data": raw_data})
        _LOGGER.info("DLMS raw test completed, results sent as event")
        
        # Создаем уведомление с результатами
        persistent_notification.async_create(
            hass,
            raw_data,
            title="Результаты DLMS необработанного теста",
            notification_id="dlms_raw_test_result"
        )
        
        # Обновляем датчик с результатами
        hass.states.async_set(
            "sensor.dlms_raw_test_result", 
            "completed", 
            {"raw_data": raw_data,
             "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")}
        )
        
        # Закрываем соединение
        dlms_data.disconnect()
        
    async def force_data_update(call: ServiceCall) -> None:
        """Внеплановое обновление данных для существующей интеграции."""
        _LOGGER.info("Forcing DLMS data update")
        
        # Проверяем, существует ли координатор
        if not hass.data.get(DOMAIN):
            _LOGGER.error("DLMS integration not set up")
            return
            
        # Получаем ID записи - если указан, используем его, иначе берем первый доступный
        entry_id = call.data.get("entry_id")
        if entry_id:
            if entry_id not in hass.data[DOMAIN]:
                _LOGGER.error("DLMS integration with ID %s not found", entry_id)
                return
            coordinator = hass.data[DOMAIN][entry_id]
        else:
            # Берем первую доступную запись
            if not hass.data[DOMAIN]:
                _LOGGER.error("No DLMS integrations found")
                return
            entry_id = next(iter(hass.data[DOMAIN]))
            coordinator = hass.data[DOMAIN][entry_id]
            
        _LOGGER.info("Forcing update for DLMS integration %s", entry_id)
        
        # Запускаем обновление
        await coordinator.async_refresh()
        _LOGGER.info("DLMS data update completed")
        
    _LOGGER.info("Registering DLMS services")
    hass.services.async_register(DOMAIN, "run_test", async_run_dlms_test, schema=TEST_DLMS_SCHEMA)
    hass.services.async_register(DOMAIN, "run_raw_test", run_raw_test, schema=TEST_DLMS_SCHEMA)
    hass.services.async_register(DOMAIN, "force_update", force_data_update)

    # Init DLMS data handler
    device_name = entry.data.get(CONF_DEVICE, "DLMS Meter")
    serial_port = entry.data.get(CONF_SERIAL_PORT, DEFAULT_SERIAL_PORT)
    query_code = entry.data.get(CONF_QUERY_CODE, DEFAULT_QUERY_CODE)
    
    # Создаем координатор обновления данных
    update_interval = timedelta(seconds=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_UPDATE_INTERVAL))
    
    dlms_data = DLMSData(
        serial_port=serial_port,
        device=device_name,
        query_code=query_code,
        baud_rate=entry.data.get(CONF_BAUDRATE, 300), # Используем 300 бод как начальную скорость
        bytesize=entry.data.get(CONF_BYTESIZE, DEFAULT_BYTESIZE),
        parity=entry.data.get(CONF_PARITY, DEFAULT_PARITY),
        stopbits=entry.data.get(CONF_STOPBITS, DEFAULT_STOPBITS),
        timeout=entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        only_listen=entry.data.get(CONF_ONLY_LISTEN, DEFAULT_ONLY_LISTEN),
        use_checksum=entry.data.get(CONF_USE_CHECKSUM, DEFAULT_USE_CHECKSUM)
    )
    coordinator = DLMSDataUpdateCoordinator(
        hass,
        dlms_data,
        update_interval,
    )
    
    # Сохраняем координатор в данных устройства
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Первый запрос данных
    _LOGGER.info("Setting up DLMS integration")
    await coordinator.async_config_entry_first_refresh()
    
    # Настройка платформ
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("DLMS integration setup completed")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading DLMS integration")
    
    # Выгрузка платформ
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Удаление данных
    if unload_ok:
        # Закрываем соединение с устройством
        coordinator = hass.data[DOMAIN][entry.entry_id]
        coordinator.dlms_data.disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)
        
    _LOGGER.info("DLMS integration unloaded")
    return unload_ok