# OrchidBot Repository Setup & Structure Guide

This document provides step-by-step instructions for developers to set up the `luhtech/orchidbot` repository, following enterprise best practices and the provided technical and architecture guidelines. All instructions are designed for long-term stability, maintainability, and security.

---

## 1. Repository Structure Overview

Clone the repository and verify the following directory and file structure:

```
orchidbot/
├── src/{controller,sensors,pumps,web}
├── config/
├── automation/
├── data/
├── tests/
├── docs/
├── scripts/
├── hardware/
├── .github/
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── requirements-rpi.txt
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
├── LICENSE
└── README.md
```

Refer to `docs/README.md` for a full description of each folder. Every new module must follow this structure.

---

## 2. Initial Setup Steps

### 2.1. Clone and Prepare

```bash
git clone https://github.com/luhtech/orchidbot.git
cd orchidbot
```

### 2.2. Python Environment

- Use **Python 3.9+**.
- Create a virtual environment:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  pip install -r requirements-dev.txt
  ```

### 2.3. Configuration Files

- Copy environment and configuration templates:
  ```bash
  cp .env.example .env
  cp config/default.yaml config/local.yaml
  ```
- All secrets and sensitive settings **must** use environment variables (see `.env.example`).

### 2.4. Hardware Verification (for Raspberry Pi)

- Run the hardware wiring verification script:
  ```bash
  python scripts/calibration/verify_wiring.py
  ```
- Follow wiring diagrams in `hardware/schematics/` and review `HARDWARE_ASSEMBLY.md` for safety-critical notes.

---

## 3. Git Workflow & PRs

- Branch naming: use `feature/*`, `fix/*`, or `docs/*` prefixes.
- Commit format: `type(scope): message` (e.g., `feat(controller): add flood cycle safety check`)
- All PRs must include:
  - `CHANGELOG.md` update
  - Test results (unit/integration/hardware/stability)
  - Performance impact notes
  - Security checklist (input validation, secrets, logs, webhooks)
  - Hardware impact assessment if applicable

---

## 4. Coding & Documentation Standards

- **Python:** PEP8, type hints, docstrings (Google style), McCabe ≤10, coverage ≥80%.
- **Security:** Validate all inputs (ADC: 0-1023), sanitize webhooks, use env vars for secrets.
- **Performance:** Sensor reads cached for 5s, batch DB writes ≤100, use asyncio for concurrency.
- **Safety:** Always cleanup GPIO, use 10s watchdog, verify relay states, log pump changes.

Refer to `docs/API_REFERENCE.md`, `docs/CALIBRATION.md`, and code samples in `docs/ai_agents/AGENT_GUIDE.md` for required patterns.

---

## 5. AI Agent & Code Automation Setup

### 5.1. AI Agent Docs

- Review and follow `docs/ai_agents/AGENT_GUIDE.md` for all code agent tasks.
- All Copilot, PR review, and automation guidelines are documented in:
  - `docs/ai_agents/COPILOT_CONTEXT.md`
  - `docs/ai_agents/CONTRIBUTION_AGENT.md`

### 5.2. PR Review

- Ensure PRs meet hardware/software safety, reliability, and security requirements.
- Document any new pin assignments or hardware changes.

---

## 6. Testing Protocol

- Run unit tests:
  ```bash
  pytest tests/unit --cov=src --cov-report=xml
  ```
- Integration tests:
  ```bash
  pytest tests/integration
  ```
- Hardware simulation tests:
  ```bash
  python tests/stability/test_suite.py quick
  ```
- Extended stability tests before major releases.
- Document all test results in `/data/test_reports/`.

---

## 7. Monitoring & Logging

- Prometheus metrics: pump_runtime, cycle_count.
- Grafana dashboards for moisture trends.
- Logs rotated daily, archived weekly, stored in `/data/logs/`.
- All events and anomalies must be logged for audit.

---

## 8. n8n/Webhooks & Workflow Automation

- n8n webhook endpoints documented in `config/n8n/`.
- All webhook events:
  - Require HMAC signatures
  - 5s timeout
  - Standardized JSON payloads
  - Logged in `/data/logs/`
- Setup n8n workflows:
  ```bash
  bash scripts/setup/setup_n8n.sh
  ```

---

## 9. Hardware Assembly & Safety

- Wiring diagrams and Bill of Materials in `hardware/schematics/` and `hardware/bom.md`
- Review `docs/HARDWARE_ASSEMBLY.md` before wiring.
- Follow all safety notes: physical overflow drains, optoisolated relays, manual override switch.

---

## 10. Community & Contribution

- Join support channels (Discord/Slack).
- Use GitHub Discussions for feature requests.
- Template configs for popular orchid species in `config/orchid_profiles.yaml`.

---

## References

- Full specification: [OrchidBot Technical Spec](https://docs.google.com/document/d/1QTA77YPErL0vsWgSZWpI53t24NAPEkp6jyYi0c7GWQQ)
- Review `docs/README.md` and all agent guides before making changes.

---

**Critical Safety Reminder:**  
Living organisms depend on this system. Always test emergency stop and overflow protection before live deployment.  
When in doubt, stop pumps & alert.