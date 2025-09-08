# OrchidBot Makefile
# Automated build, test, and deployment tasks

.PHONY: help install install-dev test test-unit test-integration test-hardware lint format type-check security-check clean setup docker run stop logs

# Default target
help:
	@echo "OrchidBot - Automated Hydroponic Orchid Cultivation System"
	@echo ""
	@echo "Available targets:"
	@echo "  setup          - Initial setup for development"
	@echo "  install        - Install production dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests"
	@echo "  test-hardware  - Run hardware simulation tests"
	@echo "  lint           - Run code linting"
	@echo "  format         - Format code with black"
	@echo "  type-check     - Run type checking with mypy"
	@echo "  security-check - Run security checks"
	@echo "  docker         - Build Docker image"
	@echo "  run            - Run the application"
	@echo "  stop           - Stop the application"
	@echo "  logs           - View application logs"
	@echo "  clean          - Clean build artifacts"

# Setup and installation
setup: clean
	@echo "Setting up OrchidBot development environment..."
	python3 -m venv venv || echo "Virtual environment already exists"
	@echo "Activate virtual environment with: source venv/bin/activate"
	@echo "Then run: make install-dev"

install:
	@echo "Installing production dependencies..."
	pip install -r requirements.txt

install-dev: install
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt
	@echo "Setting up pre-commit hooks..."
	pre-commit install || echo "Pre-commit not available"

# Testing
test: test-unit test-integration
	@echo "All tests completed"

test-unit:
	@echo "Running unit tests..."
	MOCK_HARDWARE=true LOG_LEVEL=ERROR pytest tests/unit --cov=src --cov-report=term-missing -v

test-integration:
	@echo "Running integration tests..."
	MOCK_HARDWARE=true LOG_LEVEL=ERROR pytest tests/integration -v

test-hardware:
	@echo "Running hardware simulation tests..."
	MOCK_HARDWARE=true LOG_LEVEL=ERROR python tests/stability/test_suite.py quick

test-stability:
	@echo "Running extended stability tests (this may take a while)..."
	MOCK_HARDWARE=true LOG_LEVEL=ERROR python tests/stability/test_suite.py extended

# Code quality
lint:
	@echo "Running code linting..."
	flake8 src tests --max-line-length=88 --max-complexity=10
	@echo "Linting completed"

format:
	@echo "Formatting code..."
	black src tests
	isort src tests
	@echo "Code formatting completed"

type-check:
	@echo "Running type checking..."
	mypy src --ignore-missing-imports
	@echo "Type checking completed"

security-check:
	@echo "Running security checks..."
	bandit -r src
	@echo "Security check completed"

quality-check: lint type-check security-check
	@echo "All quality checks completed"

# Docker operations
docker:
	@echo "Building Docker image..."
	docker build -t orchidbot:latest .
	@echo "Docker image built successfully"

docker-run:
	@echo "Running OrchidBot in Docker..."
	docker-compose up -d
	@echo "OrchidBot started. View logs with: make logs"

docker-stop:
	@echo "Stopping OrchidBot Docker containers..."
	docker-compose down
	@echo "OrchidBot stopped"

docker-logs:
	@echo "Viewing Docker logs..."
	docker-compose logs -f orchidbot

# Application operations
run:
	@echo "Starting OrchidBot..."
	MOCK_HARDWARE=true python -m src.core.controller

run-prod:
	@echo "Starting OrchidBot in production mode..."
	python -m src.core.controller

stop:
	@echo "Stopping OrchidBot..."
	pkill -f "python -m src.core.controller" || echo "No running processes found"

logs:
	@echo "Viewing application logs..."
	tail -f data/logs/orchidbot.log

# Hardware operations
calibrate:
	@echo "Running sensor calibration..."
	python scripts/calibration/calibrate_sensors.py

verify-wiring:
	@echo "Verifying hardware wiring..."
	python scripts/calibration/verify_wiring.py

test-pumps:
	@echo "Testing pump operations..."
	python scripts/calibration/test_pumps.py

# Maintenance
backup:
	@echo "Creating system backup..."
	bash scripts/maintenance/backup_data.sh

clean-logs:
	@echo "Cleaning old logs..."
	bash scripts/maintenance/clean_logs.sh

update:
	@echo "Updating system..."
	bash scripts/maintenance/update_system.sh

# Development helpers
dev-server:
	@echo "Starting development server with auto-reload..."
	MOCK_HARDWARE=true FLASK_ENV=development python -m src.api.flask_app

dev-watch:
	@echo "Starting development with file watching..."
	MOCK_HARDWARE=true python -m pytest-watch -- tests/unit

install-rpi:
	@echo "Installing Raspberry Pi specific dependencies..."
	pip install -r requirements-rpi.txt

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage coverage.xml htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf dist/ build/
	@echo "Cleanup completed"

# Documentation
docs:
	@echo "Generating documentation..."
	# Add sphinx or other doc generation here
	@echo "Documentation generated"

# System setup (for Raspberry Pi)
setup-rpi:
	@echo "Setting up Raspberry Pi system..."
	bash scripts/setup/configure_pi.sh

setup-systemd:
	@echo "Installing systemd service..."
	sudo bash scripts/setup/install.sh

# Environment management
env-template:
	@echo "Creating environment template..."
	cp .env.example .env
	@echo "Please edit .env with your specific settings"

config-template:
	@echo "Creating configuration template..."
	cp config/default.yaml config/local.yaml
	@echo "Please edit config/local.yaml with your specific settings"

# Git helpers
git-hooks:
	@echo "Installing Git hooks..."
	pre-commit install

# Quick start
quickstart: setup install-dev env-template config-template
	@echo ""
	@echo "🌺 OrchidBot setup complete! 🌺"
	@echo ""
	@echo "Next steps:"
	@echo "1. Activate virtual environment: source venv/bin/activate"
	@echo "2. Edit configuration: nano config/local.yaml"
	@echo "3. Edit environment: nano .env"
	@echo "4. Run tests: make test"
	@echo "5. Start application: make run"
	@echo ""
	@echo "For hardware setup, see docs/HARDWARE_ASSEMBLY.md"
	@echo "For detailed installation, see docs/INSTALLATION.md"