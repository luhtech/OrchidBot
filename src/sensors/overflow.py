"""
Overflow Sensor Manager for float switches
Critical safety component to prevent water damage
"""

import asyncio
import logging
import os
from typing import Dict, List, Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..hardware.gpio_manager import GPIOManager

logger = logging.getLogger(__name__)


class OverflowSensorManager:
    """
    Manager for overflow detection using float switches.

    Critical safety component that monitors water levels
    to prevent overflow conditions that could damage
    equipment or plants.
    """

    def __init__(self, gpio_manager: 'GPIOManager') -> None:
        """
        Initialize overflow sensor manager.

        Args:
            gpio_manager: GPIO manager instance
        """
        self.gpio_manager = gpio_manager
        self.sensor_pins = self._get_sensor_pins()
        self.last_readings: Dict[str, bool] = {}
        self.overflow_detected = False
        self.alert_callbacks: List[Callable[[str], Any]] = []

        logger.info(f"OverflowSensorManager initialized with pins: {self.sensor_pins}")

    def _get_sensor_pins(self) -> List[int]:
        """Get overflow sensor pins from environment."""
        pins_str = os.getenv("OVERFLOW_SENSOR_PINS", "21,22,23,24")
        pins = []

        for pin_str in pins_str.split(","):
            try:
                pin = int(pin_str.strip())
                pins.append(pin)
            except ValueError:
                logger.warning(f"Invalid overflow sensor pin: {pin_str}")

        return pins

    async def initialize(self) -> None:
        """Initialize overflow sensors."""
        try:
            # Setup GPIO pins as inputs with pull-up resistors
            for pin in self.sensor_pins:
                self.gpio_manager.setup_input_pin(pin, pull_up=True)

            logger.info(f"Initialized {len(self.sensor_pins)} overflow sensors")

        except Exception as e:
            logger.error(f"Failed to initialize overflow sensors: {e}")
            raise

    async def read_all(self) -> Dict[str, bool]:
        """
        Read all overflow sensors.

        Returns:
            Dict mapping sensor IDs to overflow status (True = overflow detected)
        """
        readings = {}
        overflow_detected = False

        for pin in self.sensor_pins:
            try:
                # Read sensor (float switches are typically active low)
                sensor_active = not self.gpio_manager.read_pin(pin)
                sensor_id = f"overflow_{pin}"
                readings[sensor_id] = sensor_active

                if sensor_active:
                    overflow_detected = True
                    logger.warning(f"OVERFLOW DETECTED on pin {pin}")

            except Exception as e:
                logger.error(f"Error reading overflow sensor pin {pin}: {e}")
                # Assume overflow for safety
                readings[f"overflow_{pin}"] = True
                overflow_detected = True

        # Update state
        previous_overflow = self.overflow_detected
        self.overflow_detected = overflow_detected

        # Trigger alerts if overflow state changed
        if overflow_detected and not previous_overflow:
            await self._trigger_overflow_alert()
        elif not overflow_detected and previous_overflow:
            await self._trigger_clear_alert()

        # Update cache
        self.last_readings.update(readings)
        return readings

    async def check_overflow(self) -> bool:
        """
        Quick overflow check.

        Returns:
            True if any overflow sensor is active
        """
        readings = await self.read_all()
        return any(readings.values())

    async def _trigger_overflow_alert(self) -> None:
        """Trigger overflow alert callbacks."""
        logger.critical("OVERFLOW ALERT: Water level too high!")

        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback("overflow_detected")
                else:
                    callback("overflow_detected")
            except Exception as e:
                logger.error(f"Error in overflow alert callback: {e}")

    async def _trigger_clear_alert(self) -> None:
        """Trigger overflow cleared alert."""
        logger.info("Overflow condition cleared")

        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback("overflow_cleared")
                else:
                    callback("overflow_cleared")
            except Exception as e:
                logger.error(f"Error in clear alert callback: {e}")

    def add_alert_callback(self, callback: Callable[[str], Any]) -> None:
        """
        Add callback function for overflow alerts.

        Args:
            callback: Function to call on overflow events
        """
        self.alert_callbacks.append(callback)
        logger.debug(f"Added overflow alert callback: {callback.__name__}")

    def remove_alert_callback(self, callback: Callable[[str], Any]) -> None:
        """
        Remove alert callback.

        Args:
            callback: Function to remove
        """
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
            logger.debug(f"Removed overflow alert callback: {callback.__name__}")

    def get_sensor_status(self) -> Dict:
        """Get status of all overflow sensors."""
        return {
            "sensor_pins": self.sensor_pins,
            "last_readings": self.last_readings,
            "overflow_detected": self.overflow_detected,
            "alert_callbacks_count": len(self.alert_callbacks),
        }
