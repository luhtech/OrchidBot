"""
GPIO Manager with hardware abstraction and mocking support
Critical component for safe hardware control
"""

import logging
import os
from typing import Dict, List, Optional
import threading

logger = logging.getLogger(__name__)


class MockGPIO:
    """Mock GPIO implementation for testing and development."""

    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"
    HIGH = 1
    LOW = 0
    PUD_UP = "PUD_UP"
    PUD_DOWN = "PUD_DOWN"

    def __init__(self) -> None:
        self.pin_states: Dict[int, int] = {}
        self.pin_modes: Dict[int, str] = {}
        self.setup_pins: List[int] = []

    def setmode(self, mode: str) -> None:
        logger.debug(f"MockGPIO: setmode({mode})")

    def setwarnings(self, enable: bool) -> None:
        """Mock implementation of setwarnings method."""
        logger.debug(f"MockGPIO: setwarnings({enable})")

    def setup(self, pin: int, mode: str, initial: Optional[int] = None, pull_up_down: Optional[str] = None) -> None:
        logger.debug(f"MockGPIO: setup(pin={pin}, mode={mode}, initial={initial})")
        self.setup_pins.append(pin)
        self.pin_modes[pin] = mode
        if initial is not None:
            self.pin_states[pin] = initial

    def output(self, pin: int, state: int) -> None:
        logger.debug(f"MockGPIO: output(pin={pin}, state={state})")
        self.pin_states[pin] = state

    def input(self, pin: int) -> int:
        state = self.pin_states.get(pin, 0)
        logger.debug(f"MockGPIO: input(pin={pin}) -> {state}")
        return state

    def cleanup(self) -> None:
        logger.debug("MockGPIO: cleanup()")
        self.pin_states.clear()
        self.pin_modes.clear()
        self.setup_pins.clear()


class GPIOManager:
    """
    GPIO Manager with hardware abstraction.

    Provides safe GPIO control with mocking support for development
    and testing environments.
    """

    def __init__(self, mock: bool = False):
        """
        Initialize GPIO manager.

        Args:
            mock: If True, use mock GPIO for testing
        """
        self.mock_mode = mock
        self.lock = threading.Lock()
        self.initialized = False

        if mock or os.getenv("MOCK_HARDWARE", "false").lower() == "true":
            logger.info("Using MockGPIO for testing/development")
            self.gpio = MockGPIO()
            self.mock_mode = True
        else:
            try:
                import RPi.GPIO as GPIO

                self.gpio = GPIO
                logger.info("Using real RPi.GPIO")
            except ImportError:
                logger.warning("RPi.GPIO not available, falling back to MockGPIO")
                self.gpio = MockGPIO()
                self.mock_mode = True

        self._initialize()

    def _initialize(self) -> None:
        """Initialize GPIO system."""
        with self.lock:
            if self.initialized:
                return

            try:
                # Set GPIO mode to BCM
                self.gpio.setmode(self.gpio.BCM)

                # Setup cleanup
                if not self.mock_mode:
                    self.gpio.setwarnings(False)

                self.initialized = True
                logger.info("GPIO system initialized")

            except Exception as e:
                logger.error(f"Failed to initialize GPIO: {e}")
                raise

    def _validate_pin(self, pin: int) -> None:
        """
        Validate GPIO pin number.

        Args:
            pin: GPIO pin number to validate

        Raises:
            ValueError: If pin number is invalid
        """
        if not isinstance(pin, int):
            raise ValueError(f"Pin must be an integer, got {type(pin)}")

        # Valid GPIO pins for Raspberry Pi (BCM mode)
        valid_pins = list(range(2, 28))  # GPIO 2-27 are generally available

        if pin not in valid_pins:
            raise ValueError(f"Invalid GPIO pin {pin}. Valid pins: {valid_pins}")

    def setup_output_pin(self, pin: int, initial_state: bool = False) -> None:
        """
        Setup a GPIO pin as output.

        Args:
            pin: GPIO pin number (BCM mode)
            initial_state: Initial state (True=HIGH, False=LOW)

        Raises:
            ValueError: If pin number is invalid
        """
        self._validate_pin(pin)

        with self.lock:
            try:
                initial = self.gpio.HIGH if initial_state else self.gpio.LOW
                self.gpio.setup(pin, self.gpio.OUT, initial=initial)
                logger.debug(f"Setup output pin {pin}, initial={initial_state}")

            except Exception as e:
                logger.error(f"Failed to setup output pin {pin}: {e}")
                raise

    def setup_input_pin(self, pin: int, pull_up: bool = False) -> None:
        """
        Setup a GPIO pin as input.

        Args:
            pin: GPIO pin number (BCM mode)
            pull_up: Enable internal pull-up resistor

        Raises:
            ValueError: If pin number is invalid
        """
        self._validate_pin(pin)

        with self.lock:
            try:
                pull = self.gpio.PUD_UP if pull_up else self.gpio.PUD_DOWN
                self.gpio.setup(pin, self.gpio.IN, pull_up_down=pull)
                logger.debug(f"Setup input pin {pin}, pull_up={pull_up}")

            except Exception as e:
                logger.error(f"Failed to setup input pin {pin}: {e}")
                raise

    def set_pin(self, pin: int, state: bool) -> None:
        """
        Set the state of an output pin.

        Args:
            pin: GPIO pin number
            state: True for HIGH, False for LOW

        Raises:
            ValueError: If pin number is invalid
        """
        self._validate_pin(pin)

        with self.lock:
            try:
                gpio_state = self.gpio.HIGH if state else self.gpio.LOW
                self.gpio.output(pin, gpio_state)
                logger.debug(f"Set pin {pin} to {state}")

            except Exception as e:
                logger.error(f"Failed to set pin {pin} to {state}: {e}")
                raise

    def read_pin(self, pin: int) -> bool:
        """
        Read the state of an input pin.

        Args:
            pin: GPIO pin number

        Returns:
            bool: True if HIGH, False if LOW

        Raises:
            ValueError: If pin number is invalid
        """
        self._validate_pin(pin)

        with self.lock:
            try:
                state = self.gpio.input(pin)
                result = bool(state)
                logger.debug(f"Read pin {pin}: {result}")
                return result

            except Exception as e:
                logger.error(f"Failed to read pin {pin}: {e}")
                return False

    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        with self.lock:
            try:
                if self.initialized:
                    self.gpio.cleanup()
                    self.initialized = False
                    logger.info("GPIO cleanup completed")

            except Exception as e:
                logger.error(f"Error during GPIO cleanup: {e}")

    def get_pin_states(self) -> Dict[int, bool]:
        """
        Get current states of all configured pins (mock mode only).

        Returns:
            Dict mapping pin numbers to their states
        """
        if self.mock_mode and hasattr(self.gpio, "pin_states"):
            return {pin: bool(state) for pin, state in self.gpio.pin_states.items()}
        return {}

    def is_mock_mode(self) -> bool:
        """Check if running in mock mode."""
        return self.mock_mode
