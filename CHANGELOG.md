# Changelog

All notable changes to OrchidBot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Code formatting: Fixed Black code style issues in `src/hardware/gpio_manager.py`
- CI/CD: Updated CodeQL action from @v2 to @v3 for security scanning
- CI/CD: Added explicit workflow permissions for security-events, actions, and contents
- CI/CD: Ensured PyYAML dependency is installed in documentation job before config validation

### Changed
- Enhanced CI/CD pipeline reliability and security compliance
- Improved error visibility and fail-fast behavior in workflows

## [Previous Versions]

### CI/CD Pipeline Improvements (Prior Release)
- ✅ Removed all silent error suppressions (`|| true`, `|| echo ...`)
- ✅ Added `set -e` to all multi-line shell blocks for strict error handling
- ✅ Added verbose logging throughout the workflow
- ✅ Improved error propagation in Docker tests
- ✅ Created required directories before use
- ✅ Enhanced directory validation before artifact operations
- ✅ Structured error messages with ✅/❌ indicators