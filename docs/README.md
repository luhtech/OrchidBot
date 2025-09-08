# OrchidBot Documentation

This directory contains comprehensive documentation for the OrchidBot Automated Hydroponic Orchid Cultivation System.

## Documentation Structure

- **README.md** - This overview document
- **INSTALLATION.md** - Setup and installation instructions
- **HARDWARE_ASSEMBLY.md** - Hardware assembly guide with safety notes
- **CALIBRATION.md** - Sensor calibration procedures
- **API_REFERENCE.md** - API endpoints and usage
- **TROUBLESHOOTING.md** - Common issues and solutions
- **ai_agents/** - AI code agent instructions and guidelines
- **orchid_care/** - Orchid species care guides

## Quick Start

1. **Hardware Setup**: Follow `HARDWARE_ASSEMBLY.md` for safe wiring
2. **Software Installation**: Use `INSTALLATION.md` for system setup  
3. **Calibration**: Run sensor calibration using `CALIBRATION.md`
4. **Configuration**: Edit `config/local.yaml` for your environment
5. **Testing**: Run the test suite to verify everything works

## Safety First

⚠️ **CRITICAL SAFETY REMINDER**: Living organisms depend on this system. Always test emergency stop and overflow protection before live deployment. When in doubt, stop pumps & alert.

## Core Features

### Automated Watering
- Flood-drain cycle management
- Moisture sensor monitoring
- Adaptive scheduling based on conditions
- Weather-aware watering decisions

### Safety Systems
- Emergency stop functionality
- Overflow protection with immediate shutoff
- Pump timeout mechanisms
- Hardware watchdog monitoring
- Multiple fail-safe mechanisms

### Monitoring & Control
- Real-time web dashboard
- Prometheus metrics collection
- Grafana visualization
- Mobile-responsive interface
- REST API for integration

### AI & Automation
- TensorFlow Lite plant health monitoring
- Computer vision analysis (optional)
- Predictive watering algorithms
- n8n workflow automation
- Weather API integration

### Data & Logging
- InfluxDB time-series storage
- Comprehensive event logging
- Automated data backup
- Performance metrics
- Historical trend analysis

## Hardware Requirements

### Required Components
- Raspberry Pi 4 Model B (4GB recommended)
- MicroSD card (32GB+ Class 10)
- 12V 3A power supply
- 4-channel relay module (optoisolated)
- Chirp I2C moisture sensors (4x recommended)
- Float switches for overflow detection
- 12V DC solenoid valves
- Status LEDs and resistors

### Optional Components
- Pi Camera module for visual monitoring
- DHT22 temperature/humidity sensor
- Light sensor (photodiode + ADC)
- Waterproof enclosure
- Emergency stop button

## Software Architecture

### Core Components
- **Controller** (`src/core/controller.py`) - Main orchestration
- **Safety Manager** (`src/core/safety.py`) - Critical safety systems
- **GPIO Manager** (`src/hardware/gpio_manager.py`) - Hardware abstraction
- **Sensor Managers** (`src/sensors/`) - Sensor interfaces
- **Web API** (`src/api/`) - REST API and dashboard

### Testing Framework
- Unit tests with MockGPIO for hardware-independent testing
- Integration tests for complete workflows
- Hardware simulation tests
- 24-hour stability testing
- Performance and memory monitoring

### Development Tools
- Docker containerization for easy deployment
- GitHub Actions CI/CD pipeline
- Automated code quality checks
- Security scanning
- Documentation generation

## Configuration

The system uses YAML configuration files:

- `config/default.yaml` - Default settings and documentation
- `config/local.yaml` - Your specific configuration (copy from default)
- `config/hardware.yaml` - Hardware pin mappings
- `config/orchid_profiles.yaml` - Species-specific settings

Environment variables in `.env` handle secrets and sensitive settings.

## API Endpoints

### System Status
- `GET /api/status` - System status and sensor readings
- `GET /api/health` - Health check for monitoring
- `POST /api/emergency-stop` - Trigger emergency shutdown

### Control
- `POST /api/watering/start` - Start manual watering cycle
- `POST /api/watering/stop` - Stop current watering
- `PUT /api/config` - Update configuration

### Data
- `GET /api/sensors` - Current sensor readings
- `GET /api/history` - Historical data
- `GET /api/metrics` - Prometheus metrics

### Webhooks
- `POST /webhook/orchid-system` - n8n system events
- `POST /webhook/orchid-alert` - Alert notifications

## Development Guidelines

### Coding Standards
- Python 3.9+ with type hints
- PEP 8 style guide
- Google-style docstrings
- McCabe complexity ≤ 10
- Test coverage ≥ 80%

### Safety Requirements
- All hardware control must have timeout mechanisms
- Overflow sensors must be checked before pump activation
- Emergency stop must be immediately responsive
- Fail-safe states (pumps off by default)
- Comprehensive logging for audit trails

### Testing Requirements
- Unit tests for all core functions
- MockGPIO for hardware-independent testing
- Integration tests for complete workflows
- Hardware simulation for CI/CD
- Manual testing on real hardware before release

## Community & Support

### Contributing
- Fork the repository
- Create feature branches with descriptive names
- Follow the coding standards and testing requirements
- Submit pull requests with comprehensive descriptions
- Include test results and performance impact notes

### Support Channels
- GitHub Issues for bug reports and feature requests
- GitHub Discussions for community questions
- Discord/Slack channels (see main README)

### License
MIT License - see LICENSE file for details

## Acknowledgments

This project builds on the excellent work of the open-source community:
- Raspberry Pi Foundation for the hardware platform
- The Python community for excellent libraries
- The hydroponic and orchid growing communities for knowledge sharing

---

**Remember**: This system controls living plants that depend on consistent care. Always prioritize safety and reliability over features. Test thoroughly before deploying in production environments.