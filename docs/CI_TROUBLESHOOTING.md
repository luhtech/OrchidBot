# OrchidBot CI/CD Troubleshooting Guide

## Overview

This document provides troubleshooting steps for the OrchidBot CI/CD pipeline, which has been hardened to prevent silent failures and improve error visibility.

## Recent Improvements

### Error Reporting Enhancements
- ✅ Removed all silent error suppressions (`|| true`, `|| echo ...`)
- ✅ Added `set -e` to all multi-line shell blocks for strict error handling
- ✅ Added verbose logging throughout the workflow
- ✅ Improved error propagation in Docker tests
- ✅ Created required directories before use

### Directory Structure
The CI workflow now ensures these directories exist before use:
- `data/logs/` - For application logging
- `data/test_reports/` - For test artifacts and reports
- `config/` - For configuration files

## Common Issues and Solutions

### 1. Silent Failures (RESOLVED)
**Previous Issue**: Steps would fail but continue due to `|| true` or `|| echo` patterns.
**Solution**: All error suppressions removed. Steps now fail fast on any error.

### 2. Missing Directories (RESOLVED)
**Previous Issue**: Tests would fail silently when trying to write to non-existent directories.
**Solution**: Directory creation steps added before any operations that require them.

### 3. Dependency Installation Failures (RESOLVED)
**Previous Issue**: `pip install -r requirements-dev.txt || echo "partially installed"` would hide failures.
**Solution**: Split dependency installation into separate steps that fail on error.

### 4. Test Error Propagation (RESOLVED)
**Previous Issue**: Tests could fail but not propagate exit codes properly.
**Solution**: All test scripts now use proper exit codes and `set -e` for immediate failure.

## Workflow Structure

### Main Jobs
1. **test** - Linting, formatting, type checking, unit tests, integration tests
2. **hardware-simulation** - Hardware simulation tests with mock GPIO
3. **docker-build** - Docker image build and container functionality tests
4. **security-scan** - Trivy vulnerability scanning
5. **documentation** - Documentation and configuration validation
6. **release-check** - Automated releases on version changes

### Error Handling Features
- Each multi-line shell block starts with `set -e`
- Verbose logging with step markers
- Proper exit code propagation
- Directory validation before artifact operations
- Structured error messages with ✅/❌ indicators

## Debugging Failed Builds

### Step 1: Check Workflow Logs
Look for these patterns in GitHub Actions logs:
- `❌` indicates a specific test or validation failure
- `set -e` will cause immediate job failure on any command error
- Directory creation logs show if required paths exist

### Step 2: Local Reproduction
```bash
# Recreate CI environment locally
cd /path/to/OrchidBot
mkdir -p data/logs data/test_reports config

# Test basic setup
MOCK_HARDWARE=true python -c "from src.core.controller import HydroponicController; print('✅ Controller works')"

# Run stability tests
MOCK_HARDWARE=true python tests/stability/test_suite.py quick

# Test helper scripts
python scripts/validate_config.py
python scripts/get_version.py
python scripts/test_docker_container.py
```

### Step 3: Common Failure Points
1. **Missing Dependencies**: Check pip install steps
2. **Import Errors**: Verify Python path and module structure
3. **Configuration Issues**: Run `python scripts/validate_config.py`
4. **Hardware Dependencies**: Ensure `MOCK_HARDWARE=true` is set

## Helper Scripts

The CI now uses dedicated scripts to avoid YAML parsing issues:

- `scripts/test_docker_container.py` - Docker container validation
- `scripts/validate_config.py` - YAML configuration validation
- `scripts/get_version.py` - Version extraction for releases

## Monitoring and Alerts

### Success Indicators
- All jobs show ✅ status
- Test reports are generated in `data/test_reports/`
- Artifacts are uploaded successfully
- No ❌ markers in logs

### Failure Indicators
- Jobs fail immediately on first error (no silent continuation)
- Clear error messages with ❌ markers
- Missing directories cause explicit failures
- Exit codes are properly propagated

## Enterprise Readiness Checklist

- ✅ CI pipeline fails visibly on error
- ✅ All logs and test artifacts are available for audit
- ✅ No silent error suppressions remain
- ✅ All required directories are created before use
- ✅ All tests and scripts exit non-zero on failure
- ✅ Documentation updated with CI troubleshooting steps

## Contact and Support

For CI/CD issues:
1. Check this troubleshooting guide
2. Review GitHub Actions logs for ❌ error markers
3. Test locally using the reproduction steps above
4. Check for configuration file issues with validation scripts

## Version History

- **v1.0** - Initial CI pipeline
- **v2.0** - Hardened error reporting and directory handling (current)