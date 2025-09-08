#!/bin/bash
# OrchidBot Hardware Wiring Verification Script
# Safely tests all GPIO connections without activating pumps

set -e

echo "🌺 OrchidBot Hardware Wiring Verification 🌺"
echo "=============================================="
echo ""

# Check if running on Raspberry Pi
if [[ ! -f /proc/device-tree/model ]]; then
    echo "⚠️  Warning: Not running on Raspberry Pi"
    echo "   This script is designed for Raspberry Pi hardware"
    echo "   Running in simulation mode..."
    export MOCK_HARDWARE=true
else
    PI_MODEL=$(cat /proc/device-tree/model)
    echo "✅ Detected: $PI_MODEL"
fi

echo ""
echo "Checking system requirements..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1)
echo "✅ $PYTHON_VERSION"

# Check required Python packages
echo "Checking Python dependencies..."
python3 -c "
import sys
try:
    import RPi.GPIO
    print('✅ RPi.GPIO available')
except ImportError:
    print('⚠️  RPi.GPIO not available (using mock mode)')

try:
    import smbus2
    print('✅ smbus2 available for I2C')
except ImportError:
    print('❌ smbus2 not installed - install with: pip install smbus2')

try:
    import spidev
    print('✅ spidev available for SPI')
except ImportError:
    print('❌ spidev not installed - install with: pip install spidev')
"

echo ""
echo "Testing GPIO initialization..."

# Run GPIO test
python3 << 'EOF'
import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from hardware.gpio_manager import GPIOManager

def test_gpio():
    print("Initializing GPIO manager...")
    gpio = GPIOManager(mock=os.getenv('MOCK_HARDWARE', 'false').lower() == 'true')
    
    try:
        # Test pump pins (outputs)
        pump_pins = [18, 19, 20, 26]
        print(f"Testing pump control pins: {pump_pins}")
        
        for pin in pump_pins:
            print(f"  Testing pin {pin}...")
            gpio.setup_output_pin(pin, initial_state=False)
            
            # Test state changes (but don't actually activate pumps)
            gpio.set_pin(pin, False)  # Ensure OFF (safe state)
            print(f"    Pin {pin}: OFF (safe state)")
            
            if gpio.is_mock_mode():
                # Only test state changes in mock mode
                gpio.set_pin(pin, True)
                gpio.set_pin(pin, False)
                print(f"    Pin {pin}: State change test passed")
            else:
                print(f"    Pin {pin}: Real hardware - keeping in safe state")
        
        # Test input pins
        input_pins = [21, 22, 23, 24, 25]  # Overflow sensors + emergency stop
        print(f"Testing input pins: {input_pins}")
        
        for pin in input_pins:
            print(f"  Testing input pin {pin}...")
            gpio.setup_input_pin(pin, pull_up=True)
            state = gpio.read_pin(pin)
            print(f"    Pin {pin}: {'HIGH' if state else 'LOW'}")
        
        # Test LED pins
        led_pins = [5, 6, 12, 13, 16, 17, 27]
        print(f"Testing LED pins: {led_pins}")
        
        for pin in led_pins:
            print(f"  Testing LED pin {pin}...")
            gpio.setup_output_pin(pin, initial_state=False)
            
            if gpio.is_mock_mode():
                # Flash LED in mock mode
                gpio.set_pin(pin, True)
                time.sleep(0.1)
                gpio.set_pin(pin, False)
                print(f"    LED {pin}: Flash test passed")
            else:
                # Just setup, don't flash on real hardware during verification
                print(f"    LED {pin}: Setup completed")
        
        print("✅ GPIO test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ GPIO test failed: {e}")
        return False
        
    finally:
        print("Cleaning up GPIO...")
        gpio.cleanup()

if __name__ == "__main__":
    success = test_gpio()
    if not success:
        sys.exit(1)
EOF

echo ""
echo "Testing I2C bus..."

python3 << 'EOF'
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    if os.getenv('MOCK_HARDWARE', 'false').lower() == 'true':
        print("✅ I2C test skipped in mock mode")
    else:
        import smbus2
        
        # Test I2C bus 1 (standard for Pi)
        bus = smbus2.SMBus(1)
        print("✅ I2C bus 1 accessible")
        
        # Scan for devices (common moisture sensor addresses)
        sensor_addresses = [0x20, 0x21, 0x22, 0x23]
        found_devices = []
        
        for addr in sensor_addresses:
            try:
                bus.read_byte(addr)
                found_devices.append(f"0x{addr:02x}")
            except:
                pass  # Device not found
        
        if found_devices:
            print(f"✅ Found I2C devices at: {', '.join(found_devices)}")
        else:
            print("⚠️  No moisture sensors detected (this is OK for initial setup)")
        
        bus.close()
        
except ImportError:
    print("❌ smbus2 not available - I2C functionality will not work")
except Exception as e:
    print(f"⚠️  I2C test warning: {e}")
EOF

echo ""
echo "Testing SPI bus..."

python3 << 'EOF'
import os

try:
    if os.getenv('MOCK_HARDWARE', 'false').lower() == 'true':
        print("✅ SPI test skipped in mock mode")
    else:
        import spidev
        
        # Test SPI bus 0, device 0 (standard for MCP3008)
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 1000000
        print("✅ SPI bus accessible")
        spi.close()
        
except ImportError:
    print("❌ spidev not available - ADC functionality will not work")
except Exception as e:
    print(f"⚠️  SPI test warning: {e}")
EOF

echo ""
echo "Testing configuration files..."

# Check configuration
if [[ -f "config/local.yaml" ]]; then
    echo "✅ Local configuration found"
else
    echo "⚠️  No local configuration found"
    echo "   Run: cp config/default.yaml config/local.yaml"
fi

if [[ -f ".env" ]]; then
    echo "✅ Environment file found"
else
    echo "⚠️  No environment file found"
    echo "   Run: cp .env.example .env"
fi

# Test YAML parsing
python3 -c "
import yaml
try:
    with open('config/default.yaml', 'r') as f:
        yaml.safe_load(f)
    print('✅ Configuration file is valid YAML')
except Exception as e:
    print(f'❌ Configuration file error: {e}')
"

echo ""
echo "System Summary:"
echo "==============="

# Create summary
python3 << 'EOF'
import os

mock_mode = os.getenv('MOCK_HARDWARE', 'false').lower() == 'true'

if mock_mode:
    print("🖥️  Running in MOCK mode (safe for development)")
    print("   - All GPIO operations are simulated")
    print("   - No real hardware will be affected")
    print("   - Set MOCK_HARDWARE=false for real hardware")
else:
    print("🔧 Running in HARDWARE mode")
    print("   - Real GPIO pins will be controlled")
    print("   - Ensure all wiring is correct before proceeding")
    print("   - Emergency stop should be easily accessible")

print("")
print("✅ Hardware verification completed!")
print("")
print("Next steps:")
print("1. Review any warnings above")
print("2. Check wiring diagrams in hardware/schematics/")
print("3. Test individual components with:")
print("   - python scripts/calibration/test_pumps.py")
print("   - python scripts/calibration/calibrate_sensors.py")
print("4. Run full system test with:")
print("   - make test")
print("   - python -m src.core.controller")
print("")
print("⚠️  SAFETY REMINDER:")
print("   - Test emergency stop before live operation")
print("   - Verify overflow drains are working")
print("   - Start with short test cycles")
print("   - Monitor system closely during first runs")
EOF

echo ""
echo "🌺 Verification complete! 🌺"