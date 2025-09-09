#!/usr/bin/env python3
"""
Configuration Validation Script
Validates YAML configuration files for OrchidBot
"""

import yaml

try:
    with open("config/default.yaml") as f:
        yaml.safe_load(f)
    print("✅ Configuration files are valid")
except Exception as e:
    print(f"❌ Configuration validation failed: {e}")
    raise