#!/usr/bin/env python3
"""
Version Check Script
Extracts version from pyproject.toml for CI workflow
"""

try:
    import tomllib
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
except ImportError:
    import toml
    data = toml.load("pyproject.toml")

print(data["project"]["version"])