#!/usr/bin/env python3
"""
Docker Container Test Script
Tests basic functionality of the OrchidBot controller in Docker container
"""

import sys
import os
sys.path.append("/app")

try:
    from src.core.controller import HydroponicController
    controller = HydroponicController()
    status = controller.get_status()
    assert "running" in status, "Controller status check failed"
    print("✅ Docker container test passed")
except Exception as e:
    print(f"❌ Docker container test failed: {e}")
    sys.exit(1)