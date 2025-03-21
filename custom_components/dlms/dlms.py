"""DLMS data handling."""
from __future__ import annotations

import logging
import serial
import asyncio
import time
import os
from datetime import timedelta
from typing import Any, Optional, Dict
import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_DEVICE,
    CONF_ONLY_LISTEN,
    CONF_QUERY_CODE,
    CONF_SERIAL_PORT,
    CONF_TIMEOUT,
    CONF_USE_CHECKSUM,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_DEVICE,
    DEFAULT_QUERY_CODE,
    DEFAULT_TIMEOUT,
    DEFAULT_ONLY_LISTEN,
    DEFAULT_USE_CHECKSUM,
)

_LOGGER = logging.getLogger(__name__)

class DLMSData:
    """Class to read data from DLMS device."""

    def __init__(
        self,
        serial_port: str, 
        device: str, 
        query_code: str,
        baud_rate: int = 300,
        bytesize: int = 7,
        parity: str = "E",
        stopbits: int = 1,
        timeout: int = 5,
        only_listen: bool = False,
        use_checksum: bool = True
    ) -> None:
        """Initialize DLMS data reader."""
        self.serial_port = serial_port
        self.device = device
        self.query_code = query_code
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.only_listen = only_listen
        self.use_checksum = use_checksum
        
        # Initialize port settings
        import serial
        # Bytesize settings
        if bytesize == 5:
            self.bytesize = serial.FIVEBITS
        elif bytesize == 6:
            self.bytesize = serial.SIXBITS
        elif bytesize == 7:
            self.bytesize = serial.SEVENBITS
        elif bytesize == 8:
            self.bytesize = serial.EIGHTBITS
        else:
            _LOGGER.warning("Invalid bytesize %s, defaulting to 7", bytesize)
            self.bytesize = serial.SEVENBITS
            
        # Parity settings
        if parity.upper() == "N":
            self.parity = serial.PARITY_NONE
        elif parity.upper() == "E":
            self.parity = serial.PARITY_EVEN
        elif parity.upper() == "O":
            self.parity = serial.PARITY_ODD
        elif parity.upper() == "M":
            self.parity = serial.PARITY_MARK
        elif parity.upper() == "S":
            self.parity = serial.PARITY_SPACE
        else:
            _LOGGER.warning("Invalid parity %s, defaulting to EVEN", parity)
            self.parity = serial.PARITY_EVEN
            
        # Stopbits settings
        if stopbits == 1:
            self.stopbits = serial.STOPBITS_ONE
        elif stopbits == 1.5:
            self.stopbits = serial.STOPBITS_ONE_POINT_FIVE
        elif stopbits == 2:
            self.stopbits = serial.STOPBITS_TWO
        else:
            _LOGGER.warning("Invalid stopbits %s, defaulting to 1", stopbits)
            self.stopbits = serial.STOPBITS_ONE
            
        self.serial = None
        _LOGGER.debug("DLMS initialized with port=%s, device=%s, query_code=%s, baud_rate=%d, bytesize=%s, parity=%s, stopbits=%s, timeout=%d",
                     serial_port, device, query_code, baud_rate, bytesize, parity, stopbits, timeout)
        self.parsed_data = {}
        _LOGGER.info("DLMS: Data handler initialized with port %s, device: %s, query: %s", 
                    serial_port, device, query_code)

    def connect(self) -> bool:
        """Connect to the serial port."""
        try:
            _LOGGER.info("DLMS: Connecting to serial port %s at %d baud", 
                         self.serial_port, self.baud_rate)
            
            # Check if connection already exists
            if self.serial and self.serial.is_open:
                _LOGGER.debug("DLMS: Serial port already open, closing it first")
                self.serial.close()
                time.sleep(0.5)  # Give port time to close
            
            # Initialize the port
            import serial
            self.serial = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.timeout
            )
            
            # Check if port opened
            if not self.serial.is_open:
                _LOGGER.error("DLMS: Failed to open serial port %s", self.serial_port)
                return False
                
            # Additional port information
            _LOGGER.info("DLMS: Successfully connected to %s", self.serial_port)
            _LOGGER.debug("Port settings: baudrate=%d, bytesize=%d, parity=%s, stopbits=%d, timeout=%d",
                self.serial.baudrate, self.serial.bytesize, self.serial.parity, 
                self.serial.stopbits, self.serial.timeout)
                
            # Check port access permissions
            import os, stat
            try:
                port_stat = os.stat(self.serial_port)
                mode = port_stat.st_mode
                is_readable = bool(mode & stat.S_IRUSR)
                is_writable = bool(mode & stat.S_IWUSR)
                _LOGGER.debug("Port permissions: readable=%s, writable=%s", is_readable, is_writable)
                if not (is_readable and is_writable):
                    _LOGGER.warning("Port %s may have incorrect permissions!", self.serial_port)
            except Exception as e:
                _LOGGER.warning("Could not check port permissions: %s", e)
            
            # Clear buffers
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            return True
        except Exception as e:
            _LOGGER.exception("DLMS: Error connecting to serial port %s: %s", self.serial_port, e)
            return False

    def disconnect(self) -> None:
        """Disconnect from serial port."""
        if self.serial and self.serial.is_open:
            _LOGGER.debug("DLMS: Disconnecting from serial port %s", self.serial_port)
            self.serial.close()
            _LOGGER.info("DLMS: Disconnected from serial port %s", self.serial_port)

    async def read_data_block_from_serial(self, end_byte=0x0a, start_byte=None, max_read_time=None):
        """Read data block from serial port."""
        _LOGGER.debug("Start to read data from serial port %s", self.serial.port)
        response = bytes()
        starttime = time.time()
        start_found = False
        try:
            _LOGGER.debug("Serial port settings: baudrate=%d, bytesize=%d, parity=%s, stopbits=%d, timeout=%s",
                self.serial.baudrate, self.serial.bytesize, self.serial.parity, self.serial.stopbits, self.serial.timeout)
            bytes_available = self.serial.in_waiting
            _LOGGER.debug("Bytes available before reading: %d", bytes_available)
            
            while True:
                ch = self.serial.read(1)
                runtime = time.time()
                if len(ch) == 0:
                    time_diff = runtime - starttime
                    _LOGGER.debug("No more data available after %.3f seconds", time_diff)
                    if time_diff > 3 and not response:
                        _LOGGER.debug("No initial data available")
                        return None
                    if response:
                        _LOGGER.debug("Finished reading with %d bytes after timeout", len(response))
                    break
                
                # Log each byte for debugging
                _LOGGER.debug("Read byte: %r (hex: %s, decimal: %d)", 
                    ch, ch.hex(), int.from_bytes(ch, byteorder='big') if ch else 0)
                
                if start_byte is not None:
                    if ch[0] == start_byte:
                        _LOGGER.debug("Start byte %s found, resetting response", hex(start_byte))
                        response = bytes()
                        start_found = True
                
                response += ch
                
                if ch[0] == end_byte:
                    if start_byte is not None and not start_found:
                        _LOGGER.debug("End byte found but start byte not found yet, continuing")
                        response = bytes()
                        continue
                    else:
                        _LOGGER.debug("End byte found, finished reading")
                        break
                
                if max_read_time is not None:
                    if runtime - starttime > max_read_time:
                        _LOGGER.debug("Max read time %s exceeded", max_read_time)
                        break
                        
            _LOGGER.debug("Finished reading data, received %d bytes: %r", len(response), response)
            
        except Exception as e:
            _LOGGER.exception("Exception in read_data_block_from_serial: %s", e)
            return None
            
        return response

    async def read_data(self) -> Dict[str, Dict[str, Any]]:
        """Read data from device."""
        try:
            start_time = time.time()
            
            # Reset baudrate to 300 before each read
            self.baud_rate = 300
            
            # Check connection
            if not self.serial or not self.serial.is_open:
                if not self.connect():
                    _LOGGER.error("Failed to connect to device")
                    return {}
            else:
                # If port already open, set baudrate to 300
                _LOGGER.debug("Setting baudrate to 300 for initial handshake")
                self.serial.baudrate = 300
                    
            _LOGGER.debug("Starting to read data from serial device")
            
            # Clear buffers before sending request
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            # Check port status before sending request
            in_waiting = self.serial.in_waiting
            out_waiting = self.serial.out_waiting
            _LOGGER.debug("Before request - in_waiting: %d, out_waiting: %d", in_waiting, out_waiting)
            
            # Send initialization request
            request = b"/?!\r\n"  # Standard initialization request
            _LOGGER.debug("Sending request: %r", request)
            bytes_written = self.serial.write(request)
            _LOGGER.debug("Bytes written: %d", bytes_written)
            self.serial.flush()
            
            # Check port status after sending request
            in_waiting = self.serial.in_waiting
            out_waiting = self.serial.out_waiting
            _LOGGER.debug("After request - in_waiting: %d, out_waiting: %d", in_waiting, out_waiting)
            
            # Wait before reading
            _LOGGER.debug("Waiting 1 second before reading response")
            await asyncio.sleep(1.0)
            
            # Read identification message
            _LOGGER.debug("Reading identification message")
            response = await self.read_data_block_from_serial()
            if not response:
                _LOGGER.error("No identification message received")
                return {}
            
            # Check if response is an echo of our request
            _LOGGER.debug("Response received: %r", response)
            if response == request:
                _LOGGER.debug("Request was echoed, reading actual identification message")
                # Wait more before reading
                await asyncio.sleep(0.5)
                response = await self.read_data_block_from_serial()
                if not response:
                    _LOGGER.error("No identification message received after echo")
                    return {}
            
            _LOGGER.debug("Identification message: %r", response)
            
            # Check identification message format
            if len(response) >= 7:
                try:
                    manuf_id = response[1:4].decode('ascii')
                    baud_id = chr(response[4])
                    _LOGGER.debug("Manufacturer ID: %s, Baud ID: %s", manuf_id, baud_id)
                    
                    # Determine new baudrate by identifier
                    baudrates = {
                        '0': 300, '1': 600, '2': 1200, '3': 2400,
                        '4': 4800, '5': 9600, '6': 19200
                    }
                    new_baudrate = baudrates.get(baud_id, 300)
                    
                    # Send acknowledgment and specify new baudrate
                    action = b'0'
                    ack = b'\x060' + baud_id.encode('ascii') + action + b'\r\n'
                    _LOGGER.debug("Sending ACK with baudrate %d: %r", new_baudrate, ack)
                    
                    # Wait before sending ACK
                    await asyncio.sleep(0.4)
                    
                    # Clear buffers before sending ACK
                    self.serial.reset_input_buffer()
                    self.serial.reset_output_buffer()
                    
                    bytes_written = self.serial.write(ack)
                    _LOGGER.debug("ACK bytes written: %d", bytes_written)
                    self.serial.flush()
                    
                    # Wait after sending ACK
                    await asyncio.sleep(0.4)
                    
                    # Change baudrate
                    if new_baudrate != self.baud_rate:
                        _LOGGER.debug("Switching baudrate to %d", new_baudrate)
                        self.serial.baudrate = new_baudrate
                    
                except Exception as e:
                    _LOGGER.exception("Could not parse identification message: %s", e)
                    return {}
            
            # Read OBIS data right after baudrate change
            _LOGGER.debug("Reading OBIS data from smartmeter")
            
            try:
                # Read OBIS data in chunks
                all_data = b""
                read_start_time = time.time()
                
                # Set timeout for reading
                _LOGGER.debug("Setting serial timeout to 5 seconds")
                self.serial.timeout = 5
                
                # Check if there is data before reading
                in_waiting = self.serial.in_waiting
                _LOGGER.debug("Bytes waiting in buffer before reading OBIS data: %d", in_waiting)
                
                # Read data in chunks until end marker
                while True:
                    chunk = self.serial.read(128)
                    if not chunk:
                        time_diff = time.time() - read_start_time
                        _LOGGER.debug("No more data after %.3f seconds", time_diff)
                        if not all_data:
                            _LOGGER.warning("DLMS: No data received from device")
                        break
                    
                    _LOGGER.debug("Read chunk of %d bytes: %r", len(chunk), chunk)
                    all_data += chunk
                    
                    # Check for end marker
                    if b"!\r\n" in chunk or b"\x03" in chunk:
                        _LOGGER.debug("End marker found in chunk")
                        break
                    
                    # Check timeout
                    if time.time() - read_start_time > 5:
                        _LOGGER.debug("Read timeout reached")
                        break
                
                # If no data, return empty dictionary
                if not all_data:
                    _LOGGER.warning("No OBIS data received from device")
                    return {}
                
                # Decode response to string
                try:
                    # Check for STX/ETX format
                    if len(all_data) > 3 and all_data[0] == 0x02 and 0x03 in all_data:
                        # Find ETX position
                        etx_pos = all_data.find(b'\x03')
                        decoded_data = all_data[1:etx_pos].decode('ascii', errors='replace').strip()
                        _LOGGER.debug("STX/ETX format detected, decoded data length: %d", len(decoded_data))
                    else:
                        decoded_data = all_data.decode('ascii', errors='replace').strip()
                        _LOGGER.debug("Decoded data length: %d", len(decoded_data))
                    
                    if decoded_data:
                        _LOGGER.debug("Decoded data: %s", decoded_data)
                    else:
                        _LOGGER.warning("Decoded data is empty")
                        return {}
                    
                except UnicodeDecodeError as e:
                    _LOGGER.error("Failed to decode OBIS data: %s", e)
                    return {}
                
                # Parse OBIS codes
                data = self.parse_dlms_codes(decoded_data)
                _LOGGER.debug("Finished fetching DLMS data in %.3f seconds (success: %s)", 
                             time.time() - start_time, bool(data))
                
                if not data:
                    _LOGGER.warning("Failed to parse DLMS codes")
                
                return data
            
            except Exception as e:
                _LOGGER.exception("Error reading OBIS data: %s", e)
                return {}
                
        except Exception as e:
            _LOGGER.exception("Error reading data from DLMS device: %s", e)
            return {}

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """Get parsed data."""
        return self.parsed_data

    def parse_dlms_codes(self, data: str) -> Dict[str, Dict[str, Any]]:
        """Parse DLMS codes from string data."""
        if not data:
            _LOGGER.warning("Empty data to parse")
            return {}
            
        # Split into lines
        lines = data.strip().split('\r\n')
        if not lines:
            _LOGGER.warning("No lines found in data")
            return {}
            
        result = {}
        _date = None
        _time = None
        
        # Special OBIS codes for date and time
        date_code = '0.1.3'
        time_code = '0.1.2'
            
        # Process each line
        for line in lines:
            # Skip empty lines and end marker
            if not line or line.strip() == '' or '!' in line:
                continue
                
            # Remove STX character if present
            if line and ord(line[0]) == 0x02:
                line = line[1:]
                
            try:
                # Parse line with regex
                # Format can be like: '1-1:1.8.0*255(123456.789*kWh)'
                # or with additional date/time: '1-1:1.8.1*255(123456.789*kWh)(05-09-10 11:20)'
                # Note: the regex is flexible to handle different formats
                match = re.match(r'(\d+)[-.](\d+)[.:](\d+)\.(\d+)\.(\d+)[^(]*\((.*?)\)(?:\(([^)]*)\))?', line)
                
                if match:
                    groups = match.groups()
                    # Extract the OBIS code parts
                    a, b, c, d, e = groups[0:5]
                    value_str = groups[5]
                    date_time_str = groups[6] if len(groups) > 6 else None
                    
                    # Format the OBIS code
                    short_obis_code = f"{c}.{d}.{e}"
                    
                    # Parse value and unit
                    value_parts = value_str.split('*')
                    value = value_parts[0].strip()
                    unit = value_parts[1].strip() if len(value_parts) > 1 else None
                    
                    # Try to convert to numeric
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        # Keep as string if not numeric
                        pass
                        
                    # Create result dictionary
                    result_item = {
                        'value': value
                    }
                    
                    if unit:
                        result_item['unit'] = unit
                        
                    # Check for date/time in parentheses
                    if date_time_str:
                        parts = date_time_str.split()
                        if len(parts) >= 2:
                            date_part = parts[0]
                            time_part = parts[1]
                            
                            # Store date and time for specific OBIS codes
                            if short_obis_code == date_code:
                                _date = date_part
                                result_item['date'] = date_part
                            elif short_obis_code == time_code:
                                _time = time_part
                                result_item['time'] = time_part
                            else:
                                # For other codes, add date and time as attributes
                                result_item['date'] = date_part
                                result_item['time'] = time_part
                    
                    # Add to result
                    result[short_obis_code] = result_item
                else:
                    _LOGGER.debug("Line does not match OBIS format: %s", line)
            except Exception as e:
                _LOGGER.error("Error parsing line '%s': %s", line, e)
                
        # Store date and time in results for reference
        if _date:
            result['_date'] = _date
        if _time:
            result['_time'] = _time
            
        return result

    async def run_test(self) -> str:
        """Get raw data from device.
        
        Returns raw data lines in text format.
        """
        try:
            start_time = time.time()
            # Check connection
            if not self.serial or not self.serial.is_open:
                if not self.connect():
                    _LOGGER.error("Failed to connect to device")
                    return "Error connecting to device"
            
            # Clear buffers before sending request
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            # Send initialization request
            request = b"/?!\r\n"  # Standard initialization request
            _LOGGER.debug("Sending request: %r", request)
            bytes_written = self.serial.write(request)
            _LOGGER.debug("Bytes written: %d", bytes_written)
            self.serial.flush()
            
            # Wait before reading
            await asyncio.sleep(0.5)
            
            # Read identification message
            response = await self.read_data_block_from_serial()
            if not response:
                _LOGGER.error("No identification message received")
                return "No identification message received"
                
            # Check if response is echo of our request
            if response == request:
                _LOGGER.debug("Request was echoed, reading actual identification message")
                response = await self.read_data_block_from_serial()
                if not response:
                    _LOGGER.error("No identification message received after echo")
                    return "No identification message received after echo"
                
            _LOGGER.debug("Identification message: %r", response)
            
            raw_data = "Identification message: " + response.decode('ascii', errors='replace') + "\n\n"
            
            # Check identification message format
            if len(response) >= 7:
                try:
                    manuf_id = response[1:4].decode('ascii')
                    baud_id = chr(response[4])
                    _LOGGER.debug("Manufacturer ID: %s, Baud ID: %s", manuf_id, baud_id)
                    
                    # Determine new baudrate by identifier
                    baudrates = {
                        '0': 300, '1': 600, '2': 1200, '3': 2400,
                        '4': 4800, '5': 9600, '6': 19200
                    }
                    new_baudrate = baudrates.get(baud_id, 300)
                    
                    raw_data += f"Manufacturer: {manuf_id}\n"
                    raw_data += f"Baudrate ID: {baud_id} ({new_baudrate} baud)\n\n"
                    
                    # Send acknowledgment and specify new baudrate
                    action = b'0'
                    ack = b'\x060' + baud_id.encode('ascii') + action + b'\r\n'
                    _LOGGER.debug("Sending ACK with baudrate %d: %r", new_baudrate, ack)
                    
                    # Wait before sending ACK
                    await asyncio.sleep(0.4)
                    self.serial.write(ack)
                    self.serial.flush()
                    
                    # Wait after sending ACK
                    await asyncio.sleep(0.4)
                    
                    # Change baudrate
                    if new_baudrate != self.baud_rate:
                        _LOGGER.debug("Switching baudrate to %d", new_baudrate)
                        self.serial.baudrate = new_baudrate
                    
                except Exception as e:
                    _LOGGER.warning("Could not parse identification message: %s", e)
                    raw_data += f"Error processing identification message: {str(e)}\n\n"
            
            # Read OBIS data after baudrate change
            _LOGGER.debug("Reading OBIS data from smartmeter")
            
            # Set timeout
            self.serial.timeout = 3
            
            # Read data in chunks
            all_data = b""
            read_start_time = time.time()
            
            while True:
                chunk = self.serial.read(128)
                if not chunk:
                    if not all_data:
                        _LOGGER.warning("No data received from device")
                        raw_data += "No data received from device\n"
                    break
                
                _LOGGER.debug("Read chunk: %r", chunk)
                all_data += chunk
                
                # Check for end marker
                if b"!\r\n" in chunk or b"\x03" in chunk:
                    _LOGGER.debug("End marker found")
                    break
                
                # Check timeout
                if time.time() - read_start_time > 6:
                    _LOGGER.debug("Read timeout reached")
                    break
            
            if not all_data:
                raw_data += "No OBIS data received\n"
                return raw_data
            
            # Decode response to string
            try:
                # Check for STX/ETX format
                if len(all_data) > 3 and all_data[0] == 0x02 and 0x03 in all_data:
                    # Find ETX position
                    etx_pos = all_data.find(b'\x03')
                    decoded_data = all_data[1:etx_pos].decode('ascii', errors='replace').strip()
                    _LOGGER.debug("STX/ETX format detected")
                    raw_data += "OBIS data (STX/ETX format):\n"
                else:
                    decoded_data = all_data.decode('ascii', errors='replace').strip()
                    raw_data += "OBIS data:\n"
                
                raw_data += decoded_data + "\n"
                _LOGGER.debug("Decoded data: %s", decoded_data)
            except UnicodeDecodeError as e:
                _LOGGER.error("Failed to decode data: %s", e)
                raw_data += f"Error decoding data: {str(e)}\n"
                raw_data += f"Raw bytes: {all_data!r}\n"
            
            _LOGGER.debug("Finished fetching raw DLMS data in %.3f seconds", time.time() - start_time)
            
            return raw_data
                
        except Exception as e:
            _LOGGER.error("Error executing test: %s", e)
            return f"Error executing test: {str(e)}"

class DLMSDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching DLMS data."""

    def __init__(
        self,
        hass: HomeAssistant,
        dlms_data: DLMSData,
        update_interval: timedelta = timedelta(seconds=60),
    ) -> None:
        """Initialize the data updater."""
        super().__init__(
            hass,
            _LOGGER,
            name="DLMS",
            update_interval=update_interval,
        )
        self.dlms_data = dlms_data
        _LOGGER.info("DLMS: Coordinator initialized with update interval %s", update_interval)

    async def _async_update_data(self) -> dict[str, Any] | None:
        """Fetch data from DLMS device."""
        _LOGGER.info("DLMS: Starting data update...")
        
        try:
            result = await self.dlms_data.read_data()
            
            if result:
                _LOGGER.info("DLMS: Data updated successfully")
                _LOGGER.debug("DLMS: Parsed data: %s", result)
                
                self.dlms_data.parsed_data = result
                return result
            
            _LOGGER.warning("DLMS: No data received from device")
            
            # Create notification about the problem
            if hasattr(self.hass, 'components') and hasattr(self.hass.components, 'persistent_notification'):
                from homeassistant.components import persistent_notification
                
                persistent_notification.async_create(
                    self.hass,
                    f"Error reading data from DLMS device.\n\n"
                    f"Check that the device is connected and configured correctly.",
                    title="DLMS Update Error",
                    notification_id="dlms_update_error"
                )
            
            return None

        except Exception as e:
            _LOGGER.error("DLMS: Error updating data: %s", e)
            
            # Create error notification
            if hasattr(self.hass, 'components') and hasattr(self.hass.components, 'persistent_notification'):
                from homeassistant.components import persistent_notification
                
                persistent_notification.async_create(
                    self.hass,
                    f"Error updating DLMS data: {str(e)}.\n\n"
                    f"Check logs for additional information.",
                    title="DLMS Update Error",
                    notification_id="dlms_update_error"
                )
                
            return None
