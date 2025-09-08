# AI Code Agent Guide for OrchidBot

This document provides comprehensive guidelines for AI code agents (GitHub Copilot, Claude, ChatGPT, etc.) working on the OrchidBot project.

## Project Context

OrchidBot is a **safety-critical** Raspberry Pi-based hydroponic orchid cultivation system. Living plants depend on this system for survival, making reliability and safety the highest priorities.

### System Overview
- **Hardware**: Raspberry Pi 4 controlling pumps, sensors, and safety systems
- **Purpose**: Automated flood-drain watering cycles for orchid cultivation  
- **Criticality**: Plant health depends on system reliability
- **Environment**: Indoor growing, 24/7 operation required

## Core Principles

### 1. Safety First
**ALWAYS** implement safety mechanisms:
- Pump timeouts (default 10 seconds, max 10 minutes)
- Overflow detection with immediate pump shutoff
- Emergency stop functionality
- Watchdog timers for system health
- Fail-safe GPIO states (HIGH = OFF for relays)
- Graceful cleanup on exit

### 2. Hardware Abstraction
Use the `GPIOManager` class for all hardware access:
- Supports MockGPIO for testing without hardware
- Thread-safe operations with locking
- Proper initialization and cleanup
- Error handling with fallbacks

### 3. Error Handling
Implement comprehensive error handling:
- Never crash on sensor errors (plants need water)
- Log all errors with appropriate severity
- Provide fallback behaviors
- Validate all inputs (especially sensor readings)

## Code Standards

### Python Requirements
```python
# Required style elements:
# - Type hints for all functions
# - Comprehensive docstrings (Google style)
# - PEP 8 compliance
# - McCabe complexity ≤ 10
# - Test coverage ≥ 80%

async def control_pump(pin: int, duration: float, safety_check: bool = True) -> bool:
    """
    Control a pump with safety mechanisms.
    
    Args:
        pin: GPIO pin number (BCM mode)
        duration: Runtime in seconds (max 600)
        safety_check: Whether to perform safety checks
        
    Returns:
        bool: True if operation successful
        
    Raises:
        ValueError: If duration exceeds safety limits
        HardwareError: If GPIO operation fails
    """
```

### Essential Patterns

#### 1. Hardware Control with Safety
```python
async def safe_pump_control(self, pin: int, state: bool, timeout: float = 10.0) -> bool:
    """Safe pump control with timeout and safety checks."""
    try:
        # Always check safety conditions first
        if not self.safety_manager.check_pump_safety(pin):
            logger.error(f"Safety check failed for pump {pin}")
            return False
        
        # Check for overflow before starting
        if state and await self.overflow_sensors.check_overflow():
            logger.warning("Overflow detected, cannot start pump")
            return False
        
        # Set GPIO state (active low for relays)
        self.gpio_manager.set_pin(pin, state)
        
        # Set timeout timer if turning on
        if state:
            threading.Timer(timeout, lambda: self._force_stop_pump(pin)).start()
            self.safety_manager.register_pump_start(pin, timeout)
        else:
            self.safety_manager.register_pump_stop(pin)
        
        logger.info(f"Pump {pin} {'started' if state else 'stopped'}")
        return True
        
    except Exception as e:
        logger.error(f"Pump control failed: {e}")
        # On any error, ensure pump is off
        self._force_stop_pump(pin)
        return False
```

#### 2. Sensor Reading with Validation
```python
async def read_sensor_with_retry(self, sensor_id: str, retries: int = 3) -> Optional[float]:
    """Read sensor with validation and retry logic."""
    for attempt in range(retries):
        try:
            value = await self.sensor.read(sensor_id)
            
            # Validate reading range
            if self._validate_sensor_reading(sensor_id, value):
                # Cache reading with timestamp
                self.last_readings[sensor_id] = {
                    'value': value,
                    'timestamp': time.time()
                }
                return value
            else:
                logger.warning(f"Invalid {sensor_id} reading: {value}")
                
        except Exception as e:
            logger.warning(f"Sensor read attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
    
    logger.error(f"Failed to read {sensor_id} after {retries} attempts")
    return None
```

#### 3. Emergency Shutdown
```python
async def emergency_shutdown(self, reason: str = "Unknown") -> None:
    """Execute immediate emergency shutdown."""
    logger.critical(f"EMERGENCY SHUTDOWN: {reason}")
    
    try:
        # Stop all pumps immediately
        for pin in self.pump_pins:
            self.gpio_manager.set_pin(pin, False)
            
        # Set emergency flag
        self.emergency_stop = True
        self.running = False
        
        # Notify all systems
        await self._broadcast_emergency_alert(reason)
        
        # Save system state for debugging
        await self._save_emergency_state()
        
    except Exception as e:
        logger.critical(f"Error during emergency shutdown: {e}")
        # Force GPIO cleanup as last resort
        self.gpio_manager.cleanup()
```

## Testing Requirements

### 1. MockGPIO Usage
Always use MockGPIO for unit tests:
```python
@pytest.fixture
def mock_controller():
    """Create controller with mocked hardware."""
    with patch.dict(os.environ, {'MOCK_HARDWARE': 'true'}):
        controller = HydroponicController()
        yield controller
        controller.cleanup()
```

### 2. Safety Testing
Test all safety mechanisms:
```python
@pytest.mark.asyncio
async def test_overflow_stops_pumps(mock_controller):
    """Test that overflow detection stops all pumps."""
    controller = mock_controller
    
    # Mock overflow condition
    controller.overflow_sensors.check_overflow = AsyncMock(return_value=True)
    
    # Try to start pump
    result = await controller.start_pump(18)
    
    # Should fail due to overflow
    assert result is False
    
    # Verify pump is off
    assert controller.gpio_manager.read_pin(18) is False
```

### 3. Integration Testing
Test complete workflows:
```python
@pytest.mark.asyncio
async def test_complete_watering_cycle(mock_controller):
    """Test a complete watering cycle."""
    controller = mock_controller
    
    # Set low moisture to trigger watering
    controller.last_sensor_readings = {"moisture_20": 30.0}
    
    # Execute cycle
    await controller.execute_watering_cycle()
    
    # Verify cycle completed
    assert controller.system_stats["cycle_count"] > 0
    assert controller.system_stats["last_watering"] is not None
```

## Hardware-Specific Guidelines

### GPIO Pin Assignments (BCM Mode)
```python
# Standard pin assignments (configurable via YAML)
PUMP_PINS = [18, 19, 20, 26]           # Relay control (active low)
OVERFLOW_PINS = [21, 22, 23, 24]       # Float switches (active low)
STATUS_LEDS = [5, 6, 12, 13, 16, 17, 27]  # Status indicators
EMERGENCY_STOP = 25                     # Emergency stop button
I2C_PINS = [2, 3]                      # SDA, SCL for sensors
SPI_PINS = [8, 9, 10, 11]             # CS, MISO, MOSI, CLK
```

### Timing Constraints
```python
# Critical timing parameters
PUMP_TIMEOUT_DEFAULT = 10.0      # seconds
PUMP_TIMEOUT_MAX = 600.0         # 10 minutes absolute max
SENSOR_READ_INTERVAL = 5.0       # Cache sensor readings
SAFETY_CHECK_INTERVAL = 1.0      # Safety monitoring frequency
WATCHDOG_TIMEOUT = 30.0          # System health timeout
FLOOD_DURATION = 300.0           # 5 minutes flood phase
DRAIN_DURATION = 600.0           # 10 minutes drain phase
```

## Common Anti-Patterns to Avoid

### ❌ Don't Do This
```python
# NO: Direct GPIO without safety checks
GPIO.output(18, GPIO.LOW)  # Could cause overflow

# NO: Infinite pump runtime
await start_pump(18, timeout=None)

# NO: Ignoring sensor errors
moisture = sensor.read()  # What if this fails?

# NO: Blocking operations in main loop
time.sleep(300)  # Blocks safety monitoring
```

### ✅ Do This Instead
```python
# YES: Safe GPIO with checks
if await self.safety_manager.check_all_safety_conditions():
    await self.safe_pump_control(18, True, timeout=10.0)

# YES: Always have timeouts
await start_pump(18, timeout=min(requested_time, MAX_PUMP_TIMEOUT))

# YES: Handle sensor errors gracefully
moisture = await self.read_sensor_with_retry("moisture_20")
if moisture is None:
    logger.error("Sensor failed, using last known value")
    moisture = self.last_readings.get("moisture_20", 50.0)

# YES: Non-blocking delays
await asyncio.sleep(300)  # Allows other tasks to run
```

## Configuration Management

### Environment Variables
```python
# Required environment variables
MOCK_HARDWARE = "true"           # For testing
LOG_LEVEL = "INFO"              # Logging verbosity
PUMP_PINS = "18,19,20,26"       # Hardware configuration
DATABASE_URL = "sqlite:///..."   # Data storage
WEBHOOK_SECRET = "secret"       # API security
```

### YAML Configuration
```yaml
# config/local.yaml structure
hardware:
  pumps:
    pins: [18, 19, 20, 26]
    timeout: 10.0
  sensors:
    moisture_threshold: 40.0
    target_moisture: 55.0
safety:
  watchdog_timeout: 30
  emergency_pin: 25
```

## Debugging and Monitoring

### Logging Levels
```python
logger.debug("Detailed state information")      # Development only
logger.info("Normal operation events")          # Standard operation
logger.warning("Concerning but recoverable")    # Attention needed
logger.error("Operation failed, fallback used") # Requires investigation
logger.critical("System safety compromised")    # Immediate action required
```

### Prometheus Metrics
```python
# Key metrics to track
pump_runtime_total         # Total pump operation time
cycle_count_total          # Number of watering cycles
moisture_level_current     # Current moisture readings
temperature_current        # Environmental temperature
overflow_events_total      # Safety event count
emergency_stops_total      # Critical safety events
```

## Pull Request Guidelines

### Required Checklist
- [ ] Hardware impact assessment completed
- [ ] All safety mechanisms tested
- [ ] Unit tests with MockGPIO pass
- [ ] Integration tests pass on real hardware
- [ ] 24-hour stability test completed (for major changes)
- [ ] Documentation updated
- [ ] Pin assignments documented if changed
- [ ] Performance impact assessed
- [ ] Security implications reviewed

### Testing on Hardware
```bash
# Minimum test sequence before PR
python scripts/calibration/verify_wiring.py
python -m pytest tests/unit --cov=src
python -m pytest tests/integration
python tests/stability/test_suite.py quick

# For major changes, run extended tests
python tests/stability/test_suite.py extended
```

## Emergency Procedures

### If System Becomes Unresponsive
1. **Physical emergency stop** - Press emergency stop button
2. **Power disconnect** - Unplug power supplies
3. **Manual valve operation** - Close solenoid valves manually
4. **Check overflow drains** - Verify drainage is working
5. **Debug and fix** - Use logs to identify root cause

### Recovery Procedures
1. **Check hardware connections** - Verify all wiring
2. **Test safety systems** - Verify emergency stop works
3. **Calibrate sensors** - Ensure accurate readings
4. **Run diagnostics** - Execute full test suite
5. **Gradual restart** - Monitor closely during first cycles

## Remember

- **Plant safety comes first** - Conservative decisions protect plants
- **Test thoroughly** - Especially safety mechanisms
- **Document changes** - Others need to understand your code
- **Monitor performance** - System must run 24/7 reliably
- **Keep it simple** - Complex code is harder to debug in emergencies

When in doubt, **STOP PUMPS & ALERT**. It's better to underwater briefly than to flood and kill plants.