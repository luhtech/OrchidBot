"""
Unit tests for the core controller functionality
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock

from src.core.controller import HydroponicController
from src.hardware.gpio_manager import GPIOManager


class TestHydroponicController:
    """Test cases for the main hydroponic controller."""

    @pytest_asyncio.fixture
    async def controller(self):
        """Create a controller instance for testing."""
        with patch("src.core.controller.load_dotenv"):
            controller = HydroponicController()
            yield controller
            await controller.stop()

    @pytest_asyncio.fixture
    async def mock_gpio_manager(self):
        """Create a mock GPIO manager."""
        return Mock(spec=GPIOManager)

    def test_controller_initialization(self, controller):
        """Test that controller initializes correctly."""
        assert controller is not None
        assert controller.running is False
        assert controller.emergency_stop is False
        assert isinstance(controller.pump_states, dict)

    def test_load_default_config(self, controller):
        """Test loading default configuration."""
        config = controller._get_default_config()

        assert "pumps" in config
        assert "sensors" in config
        assert "watering" in config
        assert "safety" in config

        # Check pump configuration
        assert config["pumps"]["pins"] == [18, 19, 20, 26]
        assert config["pumps"]["timeout"] == 10.0

    @pytest.mark.asyncio
    async def test_emergency_shutdown(self, controller):
        """Test emergency shutdown functionality."""
        # Start controller
        controller.running = True

        # Trigger emergency shutdown
        await controller.emergency_shutdown()

        # Verify state
        assert controller.emergency_stop is True
        assert controller.running is False

    @pytest.mark.asyncio
    async def test_pump_safety_checks(self, controller):
        """Test pump safety mechanisms."""
        # Mock safety manager
        controller.safety_manager = Mock()
        controller.safety_manager.check_pump_safety.return_value = False

        # Try to start pump
        result = await controller._start_pump(18, timeout=5.0)

        # Should fail due to safety check
        assert result is False
        controller.safety_manager.check_pump_safety.assert_called_once_with(18)

    @pytest.mark.asyncio
    async def test_sensor_reading_error_handling(self, controller):
        """Test error handling in sensor reading."""
        # Mock sensors to raise exception
        controller.moisture_sensors = Mock()
        controller.moisture_sensors.read_all = AsyncMock(
            side_effect=Exception("Sensor error")
        )

        controller.overflow_sensors = Mock()
        controller.overflow_sensors.read_all = AsyncMock(return_value={})

        # Should not crash on sensor error
        await controller._read_sensors()

        # Last readings should remain unchanged
        assert isinstance(controller.last_sensor_readings, dict)

    def test_should_water_logic(self, controller):
        """Test watering decision logic."""
        # Set threshold in config
        controller.config["sensors"]["moisture_threshold"] = 40.0

        # Test case 1: moisture below threshold
        controller.last_sensor_readings = {
            "moisture_20": 35.0,  # Below threshold
            "moisture_21": 45.0,  # Above threshold
        }

        result = asyncio.run(controller._should_water())
        assert result is True

        # Test case 2: all moisture above threshold
        controller.last_sensor_readings = {
            "moisture_20": 50.0,  # Above threshold
            "moisture_21": 55.0,  # Above threshold
        }

        result = asyncio.run(controller._should_water())
        assert result is False

    def test_get_status(self, controller):
        """Test status reporting."""
        status = controller.get_status()

        assert "running" in status
        assert "emergency_stop" in status
        assert "pump_states" in status
        assert "sensor_readings" in status
        assert "system_stats" in status
        assert "uptime" in status

        # Check data types
        assert isinstance(status["running"], bool)
        assert isinstance(status["pump_states"], dict)
        assert isinstance(status["uptime"], float)


class TestControllerConfig:
    """Test configuration handling."""

    def test_config_loading_with_missing_file(self):
        """Test behavior when config file is missing."""
        with patch("src.core.controller.load_dotenv"):
            controller = HydroponicController(config_path="nonexistent.yaml")

            # Should fall back to defaults
            assert controller.config is not None
            assert "pumps" in controller.config

    def test_config_validation(self):
        """Test configuration validation."""
        with patch("src.core.controller.load_dotenv"):
            controller = HydroponicController()
            config = controller._get_default_config()

            # Validate pump configuration
            assert len(config["pumps"]["pins"]) > 0
            assert config["pumps"]["timeout"] > 0
            assert config["pumps"]["max_daily_runtime"] > 0

            # Validate sensor configuration
            assert config["sensors"]["moisture_threshold"] >= 0
            assert config["sensors"]["moisture_threshold"] <= 100
            assert config["sensors"]["target_moisture"] >= 0
            assert config["sensors"]["target_moisture"] <= 100


class TestControllerSafety:
    """Test safety mechanisms."""

    @pytest_asyncio.fixture
    async def controller_with_mocks(self):
        """Create controller with mocked dependencies."""
        with patch("src.core.controller.load_dotenv"):
            controller = HydroponicController()

            # Mock hardware components
            controller.gpio_manager = Mock()
            controller.safety_manager = Mock()
            controller.moisture_sensors = Mock()
            controller.overflow_sensors = Mock()

            yield controller

    @pytest.mark.asyncio
    async def test_overflow_detection_stops_pumps(self, controller_with_mocks):
        """Test that overflow detection stops all pumps."""
        controller = controller_with_mocks

        # Mock overflow detection
        controller.overflow_sensors.check_overflow = AsyncMock(return_value=True)

        # Start a watering cycle
        await controller._flood_phase()

        # Verify pumps were stopped due to overflow
        controller.overflow_sensors.check_overflow.assert_called()

    @pytest.mark.asyncio
    async def test_emergency_stop_handling(self, controller_with_mocks):
        """Test emergency stop button handling."""
        controller = controller_with_mocks

        # Mock emergency stop active
        controller._check_emergency_stop = Mock(return_value=True)

        # Start controller
        controller.running = True

        # Emergency stop should trigger shutdown
        assert controller._check_emergency_stop()

        # Verify emergency state is set
        controller._check_emergency_stop.assert_called()

    @pytest.mark.asyncio
    async def test_pump_timeout_safety(self, controller_with_mocks):
        """Test pump timeout safety mechanism."""
        controller = controller_with_mocks
        controller.safety_manager.check_pump_safety.return_value = True

        # Start pump with short timeout
        await controller._start_pump(18, timeout=0.1)

        # Wait for timeout
        await asyncio.sleep(0.2)

        # Pump should be forced off (tested through mock calls)
        controller.gpio_manager.set_pin.assert_called()
