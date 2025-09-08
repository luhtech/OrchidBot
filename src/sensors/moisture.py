"""
Moisture Sensor Manager for Chirp I2C sensors
Handles calibration, reading, and data validation
"""

import asyncio
import logging
import os
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MockI2C:
    """Mock I2C implementation for testing."""
    
    def __init__(self):
        self.devices: Dict[int, Dict] = {}
        
    def write_byte(self, address: int, value: int):
        if address not in self.devices:
            self.devices[address] = {}
        logger.debug(f"MockI2C: write_byte(0x{address:02x}, 0x{value:02x})")
        
    def read_word_data(self, address: int, register: int) -> int:
        # Simulate moisture reading (0-1023 range)
        import random
        value = random.randint(200, 800)  # Typical moisture range
        logger.debug(f"MockI2C: read_word_data(0x{address:02x}, 0x{register:02x}) -> {value}")
        return value


class MoistureSensorManager:
    """
    Manager for Chirp I2C moisture sensors.
    
    Handles multiple sensors, calibration, and data validation
    with caching for performance optimization.
    """

    # Chirp sensor I2C commands
    CMD_GET_CAPACITANCE = 0x00
    CMD_SET_ADDRESS = 0x01
    CMD_GET_ADDRESS = 0x02
    CMD_MEASURE_LIGHT = 0x03
    CMD_GET_LIGHT = 0x04
    CMD_GET_TEMPERATURE = 0x05
    CMD_RESET = 0x06
    CMD_GET_VERSION = 0x07
    CMD_SLEEP = 0x08
    CMD_GET_BUSY = 0x09

    def __init__(self, bus_number: int = 1):
        """
        Initialize moisture sensor manager.
        
        Args:
            bus_number: I2C bus number (usually 1 on RPi)
        """
        self.bus_number = bus_number
        self.bus = None
        self.sensor_addresses = self._get_sensor_addresses()
        self.calibration_data: Dict[int, Tuple[int, int]] = {}  # (dry_value, wet_value)
        self.last_readings: Dict[str, float] = {}
        self.last_read_time: Dict[int, float] = {}
        self.cache_duration = 5.0  # Cache readings for 5 seconds
        self.mock_mode = os.getenv("MOCK_HARDWARE", "false").lower() == "true"
        
        logger.info(f"MoistureSensorManager initialized with addresses: {[hex(addr) for addr in self.sensor_addresses]}")

    def _get_sensor_addresses(self) -> List[int]:
        """Get sensor I2C addresses from environment."""
        addresses_str = os.getenv("MOISTURE_SENSOR_ADDRESSES", "0x20,0x21,0x22,0x23")
        addresses = []
        
        for addr_str in addresses_str.split(","):
            try:
                addr = int(addr_str.strip(), 0)  # Support both decimal and hex
                addresses.append(addr)
            except ValueError:
                logger.warning(f"Invalid sensor address: {addr_str}")
        
        return addresses

    async def initialize(self) -> None:
        """Initialize I2C bus and detect sensors."""
        try:
            if self.mock_mode:
                logger.info("Using mock I2C for testing")
                self.bus = MockI2C()
            else:
                import smbus2
                self.bus = smbus2.SMBus(self.bus_number)
                logger.info(f"I2C bus {self.bus_number} initialized")
            
            # Detect and verify sensors
            detected_sensors = await self._detect_sensors()
            logger.info(f"Detected {len(detected_sensors)} moisture sensors")
            
            # Load calibration data
            await self._load_calibration()
            
        except Exception as e:
            logger.error(f"Failed to initialize moisture sensors: {e}")
            raise

    async def _detect_sensors(self) -> List[int]:
        """Detect available sensors on the I2C bus."""
        detected = []
        
        for address in self.sensor_addresses:
            try:
                # Try to read sensor version
                if self.mock_mode:
                    detected.append(address)
                else:
                    # Send version command and try to read response
                    self.bus.write_byte(address, self.CMD_GET_VERSION)
                    await asyncio.sleep(0.1)  # Give sensor time to respond
                    version = self.bus.read_word_data(address, 0)
                    if version > 0:
                        detected.append(address)
                        logger.debug(f"Sensor at 0x{address:02x} version: {version}")
                
            except Exception as e:
                logger.debug(f"No sensor found at 0x{address:02x}: {e}")
        
        return detected

    async def read_all(self) -> Dict[str, float]:
        """
        Read all moisture sensors.
        
        Returns:
            Dict mapping sensor IDs to moisture percentages
        """
        readings = {}
        
        for address in self.sensor_addresses:
            try:
                moisture_percent = await self.read_sensor(address)
                if moisture_percent is not None:
                    sensor_id = f"moisture_{address:02x}"
                    readings[sensor_id] = moisture_percent
                    
            except Exception as e:
                logger.error(f"Error reading sensor 0x{address:02x}: {e}")
        
        # Update cache
        self.last_readings.update(readings)
        return readings

    async def read_sensor(self, address: int) -> Optional[float]:
        """
        Read a single moisture sensor.
        
        Args:
            address: I2C address of the sensor
            
        Returns:
            Moisture percentage (0-100) or None if error
        """
        current_time = time.time()
        
        # Check cache
        if (address in self.last_read_time and 
            current_time - self.last_read_time[address] < self.cache_duration):
            sensor_id = f"moisture_{address:02x}"
            return self.last_readings.get(sensor_id)
        
        try:
            # Read raw capacitance value
            if self.mock_mode:
                raw_value = self.bus.read_word_data(address, self.CMD_GET_CAPACITANCE)
            else:
                self.bus.write_byte(address, self.CMD_GET_CAPACITANCE)
                await asyncio.sleep(0.1)  # Give sensor time to measure
                raw_value = self.bus.read_word_data(address, 0)
            
            # Convert to percentage using calibration
            moisture_percent = self._convert_to_percentage(address, raw_value)
            
            # Validate reading
            if self._validate_reading(moisture_percent):
                self.last_read_time[address] = current_time
                return moisture_percent
            else:
                logger.warning(f"Invalid reading from sensor 0x{address:02x}: {moisture_percent}%")
                return None
                
        except Exception as e:
            logger.error(f"Error reading sensor 0x{address:02x}: {e}")
            return None

    def _convert_to_percentage(self, address: int, raw_value: int) -> float:
        """
        Convert raw sensor value to moisture percentage.
        
        Args:
            address: Sensor I2C address
            raw_value: Raw capacitance reading
            
        Returns:
            Moisture percentage (0-100)
        """
        # Default calibration values if not calibrated
        default_dry = 500   # Typical dry reading
        default_wet = 200   # Typical wet reading
        
        dry_value, wet_value = self.calibration_data.get(address, (default_dry, default_wet))
        
        # Convert to percentage (inverted since lower capacitance = higher moisture)
        if dry_value == wet_value:
            return 50.0  # Default if no calibration range
        
        percentage = ((dry_value - raw_value) / (dry_value - wet_value)) * 100
        
        # Clamp to 0-100 range
        return max(0.0, min(100.0, percentage))

    def _validate_reading(self, value: float) -> bool:
        """
        Validate a moisture reading.
        
        Args:
            value: Moisture percentage
            
        Returns:
            True if reading is valid
        """
        return 0.0 <= value <= 100.0

    async def calibrate_sensor(self, address: int, dry_value: int, wet_value: int) -> None:
        """
        Calibrate a moisture sensor.
        
        Args:
            address: Sensor I2C address
            dry_value: Raw reading when completely dry
            wet_value: Raw reading when fully saturated
        """
        self.calibration_data[address] = (dry_value, wet_value)
        logger.info(f"Calibrated sensor 0x{address:02x}: dry={dry_value}, wet={wet_value}")
        
        # Save calibration to file
        await self._save_calibration()

    async def _load_calibration(self) -> None:
        """Load calibration data from file."""
        try:
            import yaml
            calibration_file = "config/moisture_calibration.yaml"
            
            if os.path.exists(calibration_file):
                with open(calibration_file, 'r') as f:
                    data = yaml.safe_load(f)
                    
                for addr_str, values in data.items():
                    address = int(addr_str, 0)
                    self.calibration_data[address] = (values['dry'], values['wet'])
                    
                logger.info(f"Loaded calibration for {len(self.calibration_data)} sensors")
            else:
                logger.info("No calibration file found, using defaults")
                
        except Exception as e:
            logger.error(f"Error loading calibration: {e}")

    async def _save_calibration(self) -> None:
        """Save calibration data to file."""
        try:
            import yaml
            calibration_file = "config/moisture_calibration.yaml"
            
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(calibration_file), exist_ok=True)
            
            # Convert to serializable format
            data = {}
            for address, (dry, wet) in self.calibration_data.items():
                data[f"0x{address:02x}"] = {'dry': dry, 'wet': wet}
            
            with open(calibration_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
                
            logger.info("Calibration data saved")
            
        except Exception as e:
            logger.error(f"Error saving calibration: {e}")

    def get_sensor_status(self) -> Dict:
        """Get status of all moisture sensors."""
        return {
            "addresses": [f"0x{addr:02x}" for addr in self.sensor_addresses],
            "calibrated": [f"0x{addr:02x}" for addr in self.calibration_data.keys()],
            "last_readings": self.last_readings,
            "cache_duration": self.cache_duration,
            "mock_mode": self.mock_mode,
        }