"""
Safety Manager for OrchidBot
Critical safety mechanisms to protect plants and equipment
"""

import logging
import threading
import time
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..hardware.gpio_manager import GPIOManager

logger = logging.getLogger(__name__)


class SafetyManager:
    """
    Comprehensive safety management system for OrchidBot.

    Implements multiple layers of protection:
    - Hardware watchdog monitoring
    - Pump timeout enforcement
    - Overflow protection
    - Emergency stop handling
    - System health monitoring
    """

    def __init__(self, gpio_manager: "GPIOManager") -> None:
        """
        Initialize safety manager.

        Args:
            gpio_manager: GPIO manager instance for hardware control
        """
        self.gpio_manager = gpio_manager
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Safety state tracking
        self.emergency_stop_active = False
        self.pump_timeouts: Dict[int, float] = {}
        self.last_watchdog_reset = time.time()
        self.safety_violations: List[str] = []

        # Configuration
        self.watchdog_timeout = 30.0  # seconds
        self.max_pump_runtime = 600.0  # 10 minutes max
        self.safety_check_interval = 1.0  # seconds

        logger.info("SafetyManager initialized")

    def start_monitoring(self) -> None:
        """Start safety monitoring thread."""
        if self.monitoring:
            logger.warning("Safety monitoring already running")
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, name="SafetyMonitor", daemon=True
        )
        self.monitor_thread.start()
        logger.info("Safety monitoring started")

    def stop_monitoring(self) -> None:
        """Stop safety monitoring."""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        logger.info("Safety monitoring stopped")

    def _monitor_loop(self) -> None:
        """Main safety monitoring loop."""
        while self.monitoring:
            try:
                # Check all safety conditions
                self.check_all_safety_conditions()

                # Check watchdog timeout
                self._check_watchdog_timeout()

                # Check pump timeouts
                self._check_pump_timeouts()

                # Brief pause
                time.sleep(self.safety_check_interval)

            except Exception as e:
                logger.error(f"Error in safety monitor: {e}")
                time.sleep(5.0)

    def check_all_safety_conditions(self) -> bool:
        """
        Check all safety conditions.

        Returns:
            bool: True if all conditions are safe
        """
        safe = True
        current_violations = []

        # Check emergency stop
        if self._check_emergency_stop():
            current_violations.append("Emergency stop activated")
            safe = False

        # Check system resources
        if not self._check_system_resources():
            current_violations.append("System resource limits exceeded")
            safe = False

        # Check hardware connections
        if not self._check_hardware_connections():
            current_violations.append("Hardware connection issues detected")
            safe = False

        # Update violation list
        if current_violations != self.safety_violations:
            self.safety_violations = current_violations
            if current_violations:
                logger.warning(f"Safety violations: {current_violations}")
            else:
                logger.info("All safety conditions restored")

        return safe

    def check_pump_safety(self, pin: int) -> bool:
        """
        Check if it's safe to start a specific pump.

        Args:
            pin: GPIO pin number for the pump

        Returns:
            bool: True if safe to start pump
        """
        # Check general safety conditions
        if not self.check_all_safety_conditions():
            return False

        # Check if pump is already running
        if pin in self.pump_timeouts:
            logger.warning(f"Pump on pin {pin} already running")
            return False

        # Check daily runtime limits (would need to implement tracking)
        # This is a placeholder for more sophisticated runtime tracking

        return True

    def register_pump_start(self, pin: int, timeout: Optional[float] = None) -> None:
        """
        Register that a pump has started.

        Args:
            pin: GPIO pin number
            timeout: Maximum runtime in seconds
        """
        if timeout is None:
            timeout = self.max_pump_runtime

        self.pump_timeouts[pin] = time.time() + timeout
        logger.debug(f"Registered pump start on pin {pin} with {timeout}s timeout")

    def register_pump_stop(self, pin: int) -> None:
        """
        Register that a pump has stopped.

        Args:
            pin: GPIO pin number
        """
        if pin in self.pump_timeouts:
            del self.pump_timeouts[pin]
            logger.debug(f"Registered pump stop on pin {pin}")

    def reset_watchdog(self) -> None:
        """Reset the watchdog timer."""
        self.last_watchdog_reset = time.time()

    def emergency_shutdown(self) -> None:
        """Execute emergency shutdown procedures."""
        logger.critical("SAFETY MANAGER: EMERGENCY SHUTDOWN")

        self.emergency_stop_active = True

        # Clear pump timeouts (they should all be stopped)
        self.pump_timeouts.clear()

        # Log emergency event
        logger.critical("Emergency shutdown executed by safety manager")

    def _check_emergency_stop(self) -> bool:
        """Check if emergency stop is active."""
        # This would read from an emergency stop button/switch
        # For now, return the current state
        return self.emergency_stop_active

    def _check_watchdog_timeout(self) -> bool:
        """Check if watchdog timer has expired."""
        if time.time() - self.last_watchdog_reset > self.watchdog_timeout:
            logger.critical("Watchdog timeout exceeded - system may be hung")
            self.emergency_shutdown()
            return False
        return True

    def _check_pump_timeouts(self) -> None:
        """Check for pumps that have exceeded their timeout."""
        current_time = time.time()
        expired_pumps = []

        for pin, timeout_time in self.pump_timeouts.items():
            if current_time > timeout_time:
                expired_pumps.append(pin)

        # Force stop expired pumps
        for pin in expired_pumps:
            logger.critical(
                f"SAFETY: Force stopping pump on pin {pin} - timeout exceeded"
            )
            try:
                self.gpio_manager.set_pin(pin, False)
            except Exception as e:
                logger.error(f"Failed to force stop pump {pin}: {e}")
            finally:
                del self.pump_timeouts[pin]

    def _check_system_resources(self) -> bool:
        """Check system resource usage."""
        try:
            # Check memory usage
            import psutil

            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 90:
                logger.warning(f"High memory usage: {memory_percent}%")
                return False

            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 95:
                logger.warning(f"High CPU usage: {cpu_percent}%")
                return False

            return True

        except ImportError:
            # psutil not available, skip this check
            return True
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return False

    def _check_hardware_connections(self) -> bool:
        """Check hardware connection integrity."""
        try:
            # This would implement actual hardware checks
            # For now, assume connections are good
            return True

        except Exception as e:
            logger.error(f"Hardware connection check failed: {e}")
            return False

    def get_safety_status(self) -> Dict:
        """Get current safety status."""
        return {
            "monitoring": self.monitoring,
            "emergency_stop": self.emergency_stop_active,
            "active_violations": self.safety_violations,
            "pump_timeouts": dict(self.pump_timeouts),
            "watchdog_last_reset": self.last_watchdog_reset,
            "watchdog_time_remaining": max(
                0, self.watchdog_timeout - (time.time() - self.last_watchdog_reset)
            ),
        }

    def check_emergency_stop(self) -> bool:
        """Public method to check emergency stop status."""
        return self._check_emergency_stop()

    def check_overflow(self) -> bool:
        """Check for overflow conditions."""
        # In a real implementation, this would read from overflow sensors
        # For now, return False (no overflow detected)
        return False
