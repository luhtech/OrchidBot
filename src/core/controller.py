"""
OrchidBot Main Controller
Coordinates all system components with safety-first design
"""

import asyncio
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import yaml
from dotenv import load_dotenv

try:
    from ..hardware.gpio_manager import GPIOManager
    from ..sensors.moisture import MoistureSensorManager
    from ..sensors.overflow import OverflowSensorManager
    from .safety import SafetyManager
except ImportError:
    # Handle relative imports when running as script
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from hardware.gpio_manager import GPIOManager  # type: ignore
    from sensors.moisture import MoistureSensorManager  # type: ignore
    from sensors.overflow import OverflowSensorManager  # type: ignore
    from core.safety import SafetyManager  # type: ignore

# Load environment variables
load_dotenv()

# Configure logging safely
log_file = os.getenv("LOG_FILE", "data/logs/orchidbot.log")
log_dir = os.path.dirname(log_file)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class HydroponicController:
    """
    Main controller for the OrchidBot hydroponic system.

    Coordinates pump control, sensor monitoring, and safety systems
    with fail-safe mechanisms for plant protection.
    """

    def __init__(self, config_path: str = "config/local.yaml"):
        """
        Initialize the hydroponic controller.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.running = False
        self.emergency_stop = False

        # Initialize hardware managers
        self.gpio_manager = GPIOManager(
            mock=os.getenv("MOCK_HARDWARE", "true").lower() == "true"
        )
        self.safety_manager = SafetyManager(self.gpio_manager)
        self.moisture_sensors = MoistureSensorManager()
        self.overflow_sensors = OverflowSensorManager(self.gpio_manager)

        # System state
        self.pump_states: Dict[int, bool] = {}
        self.last_sensor_readings: Dict[str, float] = {}
        self.system_stats = {
            "start_time": datetime.now(),
            "total_runtime": 0,
            "cycle_count": 0,
            "last_watering": None,
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info("HydroponicController initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config or {}  # Ensure we return a dict, not None
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "pumps": {
                "pins": [18, 19, 20, 26],
                "timeout": 10.0,
                "max_daily_runtime": 1800,
            },
            "sensors": {
                "moisture_threshold": 40.0,
                "target_moisture": 55.0,
                "reading_interval": 5.0,
            },
            "watering": {
                "flood_duration": 300,
                "drain_duration": 600,
                "interval": 86400,
            },
            "safety": {
                "watchdog_timeout": 30,
                "emergency_pin": 25,
            },
        }

    async def start(self) -> None:
        """Start the hydroponic controller main loop."""
        if self.running:
            logger.warning("Controller already running")
            return

        logger.info("Starting OrchidBot Hydroponic Controller")
        self.running = True

        try:
            # Initialize hardware
            await self._initialize_hardware()

            # Start safety monitoring
            self.safety_manager.start_monitoring()

            # Start main control loop
            await self._main_loop()

        except Exception as e:
            logger.error(f"Critical error in controller: {e}")
            await self.emergency_shutdown()
        finally:
            await self.stop()

    async def _initialize_hardware(self) -> None:
        """Initialize all hardware components."""
        logger.info("Initializing hardware components")

        # Setup GPIO pins
        pump_pins = self.config["pumps"]["pins"]
        for pin in pump_pins:
            self.gpio_manager.setup_output_pin(pin, initial_state=False)
            self.pump_states[pin] = False

        # Setup emergency stop pin
        emergency_pin = self.config["safety"]["emergency_pin"]
        self.gpio_manager.setup_input_pin(emergency_pin, pull_up=True)

        # Initialize sensors
        await self.moisture_sensors.initialize()
        await self.overflow_sensors.initialize()

        logger.info("Hardware initialization complete")

    async def _main_loop(self) -> None:
        """Main control loop with sensor monitoring and pump control."""
        logger.info("Starting main control loop")

        while self.running and not self.emergency_stop:
            try:
                # Check emergency stop
                if self._check_emergency_stop():
                    await self.emergency_shutdown()
                    break

                # Read sensors
                await self._read_sensors()

                # Check watering needs
                if await self._should_water():
                    await self._execute_watering_cycle()

                # Safety checks
                if not self.safety_manager.check_all_safety_conditions():
                    logger.warning("Safety check failed, stopping pumps")
                    await self._stop_all_pumps()

                # Brief pause
                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5.0)

    async def _read_sensors(self) -> None:
        """Read all sensor values with caching."""
        try:
            # Read moisture sensors
            moisture_readings = await self.moisture_sensors.read_all()
            self.last_sensor_readings.update(moisture_readings)

            # Read overflow sensors
            overflow_status = await self.overflow_sensors.read_all()
            self.last_sensor_readings.update(overflow_status)

            # Log readings periodically
            if int(time.time()) % 60 == 0:  # Every minute
                logger.info(f"Sensor readings: {self.last_sensor_readings}")

        except Exception as e:
            logger.error(f"Error reading sensors: {e}")

    async def _should_water(self) -> bool:
        """
        Determine if watering is needed based on sensor readings.

        Returns:
            bool: True if watering cycle should start
        """
        # Check if any moisture sensor is below threshold
        moisture_threshold = self.config["sensors"]["moisture_threshold"]

        for sensor_id, reading in self.last_sensor_readings.items():
            if sensor_id.startswith("moisture_") and reading < moisture_threshold:
                logger.info(
                    f"Watering needed: {sensor_id} = {reading}% < {moisture_threshold}%"
                )
                return True

        return False

    async def _execute_watering_cycle(self) -> None:
        """Execute a complete flood-drain watering cycle."""
        logger.info("Starting watering cycle")

        try:
            # Pre-flight safety checks
            if not self.safety_manager.check_all_safety_conditions():
                logger.error("Safety check failed, aborting watering cycle")
                return

            # Flood phase
            await self._flood_phase()

            # Drain phase
            await self._drain_phase()

            # Update statistics
            cycle_count = self.system_stats.get("cycle_count", 0)
            if isinstance(cycle_count, int):
                self.system_stats["cycle_count"] = cycle_count + 1
            else:
                self.system_stats["cycle_count"] = 1
            self.system_stats["last_watering"] = datetime.now()

            logger.info("Watering cycle completed successfully")

        except Exception as e:
            logger.error(f"Error in watering cycle: {e}")
            await self._stop_all_pumps()

    async def _flood_phase(self) -> None:
        """Execute flooding phase of watering cycle."""
        flood_duration = self.config["watering"]["flood_duration"]
        logger.info(f"Starting flood phase for {flood_duration} seconds")

        # Start pumps with timeout safety
        for pin in self.config["pumps"]["pins"]:
            if await self._start_pump(pin, timeout=flood_duration):
                self.pump_states[pin] = True

        # Monitor for flood duration
        start_time = time.time()
        while time.time() - start_time < flood_duration:
            # Check for overflow
            if await self.overflow_sensors.check_overflow():
                logger.warning("Overflow detected, stopping flood phase")
                break

            # Check emergency conditions
            if self._check_emergency_stop():
                break

            await asyncio.sleep(1.0)

        # Stop all pumps
        await self._stop_all_pumps()
        logger.info("Flood phase completed")

    async def _drain_phase(self) -> None:
        """Execute draining phase of watering cycle."""
        drain_duration = self.config["watering"]["drain_duration"]
        logger.info(f"Starting drain phase for {drain_duration} seconds")

        # Wait for drainage (pumps off)
        await asyncio.sleep(drain_duration)

        logger.info("Drain phase completed")

    async def _start_pump(self, pin: int, timeout: float = 10.0) -> bool:
        """
        Start a pump with safety checks and timeout.

        Args:
            pin: GPIO pin number for the pump
            timeout: Maximum runtime in seconds

        Returns:
            bool: True if pump started successfully
        """
        try:
            # Safety checks
            if not self.safety_manager.check_pump_safety(pin):
                logger.error(f"Safety check failed for pump on pin {pin}")
                return False

            # Start pump (active low for relays)
            self.gpio_manager.set_pin(pin, True)

            # Set timeout timer
            threading.Timer(timeout, lambda: self._force_stop_pump(pin)).start()

            logger.info(f"Pump started on pin {pin} with {timeout}s timeout")
            return True

        except Exception as e:
            logger.error(f"Failed to start pump on pin {pin}: {e}")
            return False

    def _force_stop_pump(self, pin: int) -> None:
        """Force stop a pump (timeout safety mechanism)."""
        logger.warning(f"Force stopping pump on pin {pin} due to timeout")
        self.gpio_manager.set_pin(pin, False)
        self.pump_states[pin] = False

    async def _stop_all_pumps(self) -> None:
        """Stop all pumps immediately."""
        logger.info("Stopping all pumps")

        for pin in self.config["pumps"]["pins"]:
            self.gpio_manager.set_pin(pin, False)
            self.pump_states[pin] = False

    def _check_emergency_stop(self) -> bool:
        """Check if emergency stop is activated."""
        emergency_pin = self.config["safety"]["emergency_pin"]
        emergency_active = not self.gpio_manager.read_pin(emergency_pin)  # Active low

        if emergency_active and not self.emergency_stop:
            logger.critical("EMERGENCY STOP ACTIVATED")
            self.emergency_stop = True

        return emergency_active

    async def emergency_shutdown(self) -> None:
        """Execute emergency shutdown procedure."""
        logger.critical("EXECUTING EMERGENCY SHUTDOWN")

        # Stop all pumps immediately
        await self._stop_all_pumps()

        # Set emergency flag
        self.emergency_stop = True

        # Stop main loop
        self.running = False

        # Notify safety manager
        self.safety_manager.emergency_shutdown()

    async def stop(self) -> None:
        """Gracefully stop the controller."""
        logger.info("Stopping OrchidBot Controller")
        self.running = False

        # Stop all pumps
        await self._stop_all_pumps()

        # Cleanup hardware
        self.gpio_manager.cleanup()

        # Stop safety monitoring
        self.safety_manager.stop_monitoring()

        logger.info("Controller stopped")

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown")
        asyncio.create_task(self.stop())

    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "running": self.running,
            "emergency_stop": self.emergency_stop,
            "pump_states": self.pump_states,
            "sensor_readings": self.last_sensor_readings,
            "system_stats": self.system_stats,
            "uptime": (
                datetime.now()
                - (
                    self.system_stats["start_time"]
                    if isinstance(self.system_stats["start_time"], datetime)
                    else datetime.now()
                )
            ).total_seconds(),
        }


async def main() -> None:
    """Main entry point for OrchidBot controller."""
    controller = HydroponicController()

    try:
        await controller.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.critical(f"Critical error: {e}")
    finally:
        await controller.stop()


if __name__ == "__main__":
    asyncio.run(main())
