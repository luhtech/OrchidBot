# 🌺 OrchidBot - Automated Hydroponic Orchid Cultivation System

[![CI](https://github.com/luhtech/OrchidBot/actions/workflows/ci.yml/badge.svg)](https://github.com/luhtech/OrchidBot/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/luhtech/OrchidBot/branch/main/graph/badge.svg)](https://codecov.io/gh/luhtech/OrchidBot)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A comprehensive Raspberry Pi-based hydroponic system for automated orchid cultivation with AI-powered plant health monitoring, flood-drain watering cycles, and enterprise-grade safety mechanisms.

## 🚀 Features

### 💧 Automated Watering
- **Flood-drain cycles** with precise timing control
- **Moisture sensor monitoring** using Chirp I2C sensors
- **Adaptive scheduling** based on environmental conditions
- **Weather-aware watering** with OpenWeatherMap integration

### 🛡️ Safety Systems
- **Emergency stop** functionality with physical button
- **Overflow protection** with immediate pump shutoff
- **Pump timeout mechanisms** preventing equipment damage
- **Hardware watchdog** monitoring for system health
- **Multiple fail-safe mechanisms** protecting plants and equipment

### 📊 Monitoring & Control
- **Real-time web dashboard** with mobile-responsive design
- **Prometheus metrics** collection for system monitoring
- **Grafana dashboards** for data visualization
- **REST API** for integration with external systems
- **Comprehensive logging** with rotation and archival

### 🤖 AI & Automation
- **TensorFlow Lite** plant health monitoring
- **Computer vision** analysis with Pi Camera (optional)
- **Predictive watering** algorithms
- **n8n workflow automation** for complex scenarios
- **MQTT integration** for IoT platforms

## 🛠️ Quick Start

### Prerequisites
- Raspberry Pi 4 Model B (4GB recommended)
- Python 3.9 or higher
- MicroSD card (32GB+ Class 10)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/luhtech/OrchidBot.git
   cd OrchidBot
   ```

2. **Quick setup**
   ```bash
   make quickstart
   source venv/bin/activate
   ```

3. **Configure the system**
   ```bash
   # Edit configuration files
   nano config/local.yaml
   nano .env
   ```

4. **Verify hardware (Raspberry Pi only)**
   ```bash
   python scripts/calibration/verify_wiring.py
   ```

5. **Run tests**
   ```bash
   make test
   ```

6. **Start the system**
   ```bash
   make run
   ```

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f orchidbot

# Stop services
docker-compose down
```

## 📖 Documentation

- **[Setup Guide](SETUP_GUIDE.md)** - Complete repository setup instructions
- **[Installation Guide](docs/INSTALLATION.md)** - Detailed installation steps
- **[Hardware Assembly](docs/HARDWARE_ASSEMBLY.md)** - Wiring and safety guidelines
- **[API Reference](docs/API_REFERENCE.md)** - REST API documentation
- **[AI Agent Guide](docs/ai_agents/AGENT_GUIDE.md)** - Guidelines for AI code assistants

## 🔧 Hardware Requirements

### Required Components
- Raspberry Pi 4 Model B (4GB)
- 12V 3A power supply
- 4-channel optoisolated relay module
- Chirp I2C moisture sensors (4x)
- Float switches for overflow detection
- 12V DC normally-closed solenoid valves
- Status LEDs and resistors

### Optional Components
- Pi Camera module for visual monitoring
- DHT22 temperature/humidity sensor
- Light sensor with ADC
- Emergency stop button
- Waterproof enclosure

See [hardware/bom.md](hardware/bom.md) for complete bill of materials.

## 📁 Repository Structure

```
OrchidBot/
├── src/                    # Source code
│   ├── core/              # Main controller and safety systems
│   ├── hardware/          # GPIO and hardware abstraction
│   ├── sensors/           # Sensor interfaces
│   ├── api/               # Web API and dashboard
│   └── integrations/      # External service integrations
├── config/                # Configuration files
├── hardware/              # Wiring diagrams and 3D models
├── tests/                 # Comprehensive test suite
├── docs/                  # Documentation
├── scripts/               # Setup and maintenance scripts
└── data/                  # Logs and data storage
```

## 🧪 Testing

```bash
# Run all tests
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration

# Hardware simulation
make test-hardware

# 24-hour stability test
make test-stability
```

## 🔒 Security

- Environment variables for all secrets
- HMAC webhook authentication
- Input validation and sanitization
- Secure Docker configuration
- Regular security scanning with Bandit

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following our [coding standards](docs/ai_agents/AGENT_GUIDE.md)
4. Run tests and ensure they pass
5. Submit a pull request

### PR Requirements
- [ ] Hardware impact assessment
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Security checklist completed
- [ ] Performance impact noted

## 📊 Monitoring

### Web Dashboard
Access the dashboard at `http://your-pi-ip:5000`

### Grafana Dashboards
Monitor system metrics at `http://your-pi-ip:3000`
- Default login: `admin/orchidbot123`

### Prometheus Metrics
System metrics available at `http://your-pi-ip:9090`

## 🌱 Orchid Care Profiles

The system includes pre-configured profiles for popular orchid species:

- **Phalaenopsis** (Moth Orchids) - Moderate moisture, warm conditions
- **Cattleya** - Lower moisture, bright light requirements  
- **Dendrobium** - Seasonal watering variations
- **Oncidium** - Consistent moisture, good drainage

See [config/orchid_profiles.yaml](config/orchid_profiles.yaml) for details.

## ⚠️ Safety Notice

**CRITICAL**: This system controls living plants that depend on consistent care. Always:

- Test emergency stop and overflow protection before live deployment
- Verify all wiring matches the provided diagrams
- Start with short test cycles and monitor closely
- Have physical backup drainage systems
- Keep the system easily accessible for manual intervention

**When in doubt, stop pumps and alert.**

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Raspberry Pi Foundation for the excellent hardware platform
- The Python community for robust libraries
- Hydroponic and orchid growing communities for sharing knowledge
- Contributors and testers who help make this system reliable

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/luhtech/OrchidBot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/luhtech/OrchidBot/discussions)
- **Wiki**: [Project Wiki](https://github.com/luhtech/OrchidBot/wiki)

---

Made with 💚 for orchid enthusiasts and automation lovers.

**Happy Growing! 🌺**
