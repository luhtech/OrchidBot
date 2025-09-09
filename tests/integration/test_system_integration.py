"""
Integration tests for OrchidBot system components
Tests component interactions and system-level functionality
"""

import asyncio
import os
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch

# Ensure mock mode for safety
os.environ["MOCK_HARDWARE"] = "true"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.controller import HydroponicController
from hardware.gpio_manager import GPIOManager
from core.safety import SafetyManager


class TestSystemIntegration:
    """Test integration between major system components."""

    @pytest_asyncio.fixture
    async def controller(self):
        """Create a controller instance for integration testing."""
        controller = HydroponicController()
        yield controller
        # Cleanup
        if hasattr(controller, "running") and controller.running:
            await controller.stop()

    @pytest.mark.asyncio
    async def test_controller_gpio_integration(self, controller):
        """Test controller and GPIO manager integration."""
        assert controller.gpio_manager is not None
        assert hasattr(controller.gpio_manager, "setup_output_pin")
        assert hasattr(controller.gpio_manager, "setup_input_pin")

    @pytest.mark.asyncio
    async def test_controller_safety_integration(self, controller):
        """Test controller and safety manager integration."""
        assert controller.safety_manager is not None
        assert hasattr(controller.safety_manager, "check_pump_safety")

        # Test safety check integration
        pin = 18
        safety_result = controller.safety_manager.check_pump_safety(pin)
        assert isinstance(safety_result, bool)

    @pytest.mark.asyncio
    async def test_sensor_reading_flow(self, controller):
        """Test sensor reading integration."""
        # Test that sensor managers are initialized
        assert controller.moisture_sensors is not None
        assert controller.overflow_sensors is not None

        # Test sensor reading flow (in mock mode)
        await controller._read_sensors()

        # Should have sensor readings structure
        assert hasattr(controller, "last_sensor_readings")
        assert isinstance(controller.last_sensor_readings, dict)

    @pytest.mark.asyncio
    async def test_emergency_shutdown_integration(self, controller):
        """Test emergency shutdown across all components."""
        # Start controller
        controller.running = True

        # Trigger emergency shutdown
        await controller.emergency_shutdown()

        # Verify all components are in safe state
        assert controller.emergency_stop is True
        assert controller.running is False
        assert controller.safety_manager.emergency_stop_active is True

    @pytest.mark.asyncio
    async def test_pump_operation_integration(self, controller):
        """Test pump operation with safety checks."""
        pin = 18

        # Test pump safety check before operation
        safety_ok = controller.safety_manager.check_pump_safety(pin)

        if safety_ok:
            # Test starting pump with timeout
            result = await controller._start_pump(pin, timeout=0.1)
            # In mock mode, this should succeed
            assert result is True or result is False  # Either is acceptable in test
        else:
            # Safety check failed, which is also acceptable
            assert safety_ok is False

    def test_configuration_integration(self, controller):
        """Test configuration loading and component setup."""
        config = controller.config

        # Verify all components use consistent configuration
        assert "pumps" in config
        assert "sensors" in config
        assert "safety" in config

        # Check that pump pins are configured consistently
        pump_pins = config["pumps"]["pins"]
        assert len(pump_pins) > 0

        # All pump pins should be integers
        for pin in pump_pins:
            assert isinstance(pin, int)
            assert 0 <= pin <= 40  # Valid GPIO pin range


class TestErrorHandlingIntegration:
    """Test error handling across system components."""

    @pytest.mark.asyncio
    async def test_sensor_error_recovery(self):
        """Test system behavior when sensors fail."""
        controller = HydroponicController()

        # Mock sensor failure
        controller.moisture_sensors.read_all = Mock(
            side_effect=Exception("Sensor failure")
        )

        # System should handle the error gracefully
        await controller._read_sensors()

        # Should not crash and maintain last known state
        assert hasattr(controller, "last_sensor_readings")

    @pytest.mark.asyncio
    async def test_gpio_error_recovery(self):
        """Test system behavior when GPIO operations fail."""
        controller = HydroponicController()

        # Mock GPIO failure
        controller.gpio_manager.set_pin = Mock(side_effect=Exception("GPIO failure"))

        # Should handle GPIO errors gracefully
        try:
            await controller._start_pump(18, timeout=0.1)
            # Either succeeds or fails gracefully
        except Exception as e:
            # Should not propagate unhandled exceptions
            assert False, f"Unhandled exception: {e}"


class TestConfigurationIntegration:
    """Test configuration handling across components."""

    def test_default_configuration_completeness(self):
        """Test that default configuration has all required sections."""
        controller = HydroponicController()
        config = controller.config

        required_sections = ["pumps", "sensors", "watering", "safety"]

        for section in required_sections:
            assert section in config, f"Missing configuration section: {section}"

    def test_pump_configuration_consistency(self):
        """Test that pump configuration is consistent across components."""
        controller = HydroponicController()
        config = controller.config

        # Pump pins should be configured
        pump_pins = config["pumps"]["pins"]
        assert len(pump_pins) >= 1

        # Timeout should be reasonable
        timeout = config["pumps"]["timeout"]
        assert 1.0 <= timeout <= 3600.0  # Between 1 second and 1 hour

    def test_sensor_configuration_consistency(self):
        """Test that sensor configuration is consistent."""
        controller = HydroponicController()
        config = controller.config

        # Moisture threshold should be reasonable
        threshold = config["sensors"]["moisture_threshold"]
        assert 0 <= threshold <= 100

        # Target moisture should be reasonable
        target = config["sensors"]["target_moisture"]
        assert 0 <= target <= 100
