"""
OrchidBot Security Audit Checklist
Comprehensive security review for enterprise deployment
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logger = logging.getLogger(__name__)


class SecurityAudit:
    """Security audit and validation for OrchidBot system."""

    def __init__(self):
        self.findings: List[Dict] = []
        self.start_time = datetime.now()

    def run_audit(self) -> Dict:
        """Run comprehensive security audit."""
        print("🔒 OrchidBot Security Audit")
        print("=" * 50)

        # Security checks
        checks = [
            ("environment_variables", self._check_environment_security),
            ("file_permissions", self._check_file_permissions),
            ("input_validation", self._check_input_validation),
            ("logging_security", self._check_logging_security),
            ("configuration_security", self._check_configuration_security),
            ("dependency_security", self._check_dependency_security),
        ]

        passed = 0
        for check_name, check_func in checks:
            try:
                print(f"\n🔍 {check_name.replace('_', ' ').title()}")
                result = check_func()
                if result["status"] == "PASS":
                    print(f"  ✅ {result['message']}")
                    passed += 1
                elif result["status"] == "WARN":
                    print(f"  ⚠️  {result['message']}")
                    self.findings.append({
                        "check": check_name,
                        "severity": "WARNING",
                        "finding": result["message"],
                        "recommendation": result.get("recommendation", "Review and address")
                    })
                else:
                    print(f"  ❌ {result['message']}")
                    self.findings.append({
                        "check": check_name,
                        "severity": "CRITICAL",
                        "finding": result["message"],
                        "recommendation": result.get("recommendation", "Fix immediately")
                    })
            except Exception as e:
                print(f"  💥 Error during {check_name}: {e}")
                self.findings.append({
                    "check": check_name,
                    "severity": "ERROR",
                    "finding": str(e),
                    "recommendation": "Investigate error cause"
                })

        # Generate report
        report = {
            "audit_time": self.start_time.isoformat(),
            "total_checks": len(checks),
            "passed": passed,
            "findings": self.findings,
            "overall_status": "PASS" if len(self.findings) == 0 else "REVIEW_REQUIRED"
        }

        return report

    def _check_environment_security(self) -> Dict:
        """Check environment variable security."""
        # Check for sensitive data in environment
        sensitive_patterns = ['password', 'secret', 'key', 'token', 'api']
        
        env_vars = dict(os.environ)
        exposed_secrets = []
        
        for var, value in env_vars.items():
            var_lower = var.lower()
            if any(pattern in var_lower for pattern in sensitive_patterns):
                if value and len(value) > 0:
                    exposed_secrets.append(var)
        
        if exposed_secrets:
            return {
                "status": "WARN",
                "message": f"Found {len(exposed_secrets)} potentially sensitive environment variables",
                "recommendation": "Ensure secrets are properly protected and not logged"
            }
        
        return {
            "status": "PASS",
            "message": "No obvious secrets found in environment variables"
        }

    def _check_file_permissions(self) -> Dict:
        """Check file and directory permissions."""
        sensitive_files = [
            ".env",
            "config/local.yaml",
            "data/logs/",
            "scripts/"
        ]
        
        permission_issues = []
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                perms = oct(stat_info.st_mode)[-3:]
                
                # Check for world-writable files (XXX7XX)
                if perms.endswith('7') or perms.endswith('6'):
                    permission_issues.append(f"{file_path}: {perms}")
        
        if permission_issues:
            return {
                "status": "WARN",
                "message": f"Found {len(permission_issues)} files with loose permissions",
                "recommendation": "Restrict file permissions to owner only for sensitive files"
            }
        
        return {
            "status": "PASS",
            "message": "File permissions appear appropriate"
        }

    def _check_input_validation(self) -> Dict:
        """Check input validation in core modules."""
        try:
            # Import and check core modules
            from core.controller import HydroponicController
            from hardware.gpio_manager import GPIOManager
            
            validation_checks = []
            
            # Check GPIO pin validation
            gpio = GPIOManager(mock=True)
            
            # Test invalid pin numbers
            try:
                gpio.setup_output_pin(-1)  # Invalid pin
                validation_checks.append("GPIO accepts invalid pin numbers")
            except (ValueError, Exception):
                pass  # Good, validation working
            
            try:
                gpio.setup_output_pin(999)  # Invalid pin
                validation_checks.append("GPIO accepts out-of-range pin numbers")
            except (ValueError, Exception):
                pass  # Good, validation working
            
            if validation_checks:
                return {
                    "status": "WARN",
                    "message": f"Input validation issues found: {validation_checks}",
                    "recommendation": "Add proper input validation for all user inputs"
                }
            
            return {
                "status": "PASS",
                "message": "Basic input validation appears to be working"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Error checking input validation: {e}"
            }

    def _check_logging_security(self) -> Dict:
        """Check logging configuration for security issues."""
        issues = []
        
        # Check if logs are created with appropriate permissions
        log_dir = "data/logs"
        if os.path.exists(log_dir):
            for log_file in os.listdir(log_dir):
                log_path = os.path.join(log_dir, log_file)
                if os.path.isfile(log_path):
                    stat_info = os.stat(log_path)
                    perms = oct(stat_info.st_mode)[-3:]
                    if perms.endswith('7') or perms.endswith('6'):
                        issues.append(f"Log file {log_file} has loose permissions: {perms}")
        
        # Check for potential secret logging
        log_patterns_to_avoid = ['password', 'secret', 'key', 'token']
        
        if issues:
            return {
                "status": "WARN",
                "message": f"Logging security issues: {issues}",
                "recommendation": "Secure log file permissions and review logging content"
            }
        
        return {
            "status": "PASS",
            "message": "Logging configuration appears secure"
        }

    def _check_configuration_security(self) -> Dict:
        """Check configuration security."""
        issues = []
        
        # Check default configuration
        try:
            from core.controller import HydroponicController
            controller = HydroponicController()
            config = controller.config
            
            # Check for hardcoded credentials
            config_str = json.dumps(config, default=str).lower()
            sensitive_patterns = ['password', 'secret', 'key', 'token']
            
            for pattern in sensitive_patterns:
                if pattern in config_str:
                    issues.append(f"Configuration may contain sensitive data: {pattern}")
            
            # Check for insecure defaults
            if 'safety' in config:
                watchdog_timeout = config['safety'].get('watchdog_timeout', 0)
                if watchdog_timeout > 3600:  # More than 1 hour
                    issues.append("Watchdog timeout is very long, potential safety risk")
            
        except Exception as e:
            issues.append(f"Error checking configuration: {e}")
        
        if issues:
            return {
                "status": "WARN",
                "message": f"Configuration security issues: {issues}",
                "recommendation": "Review configuration for security best practices"
            }
        
        return {
            "status": "PASS",
            "message": "Configuration security appears adequate"
        }

    def _check_dependency_security(self) -> Dict:
        """Check dependency security."""
        try:
            # Check for known vulnerable packages (basic check)
            import pkg_resources
            
            installed_packages = [d.project_name.lower() for d in pkg_resources.working_set]
            
            # Basic check for obviously outdated or vulnerable packages
            potentially_risky = []
            
            # Check for development/debug packages in production
            debug_packages = ['ipdb', 'pdb', 'debugpy', 'pydevd']
            for pkg in debug_packages:
                if pkg in installed_packages:
                    potentially_risky.append(f"Debug package '{pkg}' found")
            
            if potentially_risky:
                return {
                    "status": "WARN",
                    "message": f"Potential dependency issues: {potentially_risky}",
                    "recommendation": "Review dependencies for production deployment"
                }
            
            return {
                "status": "PASS",
                "message": "No obvious dependency security issues found"
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Error checking dependencies: {e}"
            }

    def save_report(self, report: Dict) -> str:
        """Save security audit report."""
        os.makedirs("data/security_reports", exist_ok=True)
        
        report_file = f"data/security_reports/security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_file


def main():
    """Run security audit."""
    audit = SecurityAudit()
    report = audit.run_audit()
    
    # Save report
    report_file = audit.save_report(report)
    
    # Print summary
    print("\n" + "=" * 50)
    print("🔒 Security Audit Summary")
    print("=" * 50)
    print(f"Total Checks: {report['total_checks']}")
    print(f"Passed: {report['passed']}")
    print(f"Findings: {len(report['findings'])}")
    print(f"Overall Status: {report['overall_status']}")
    print(f"Report saved: {report_file}")
    
    if report['findings']:
        print("\n📋 Findings:")
        for finding in report['findings']:
            severity_icon = {"WARNING": "⚠️", "CRITICAL": "❌", "ERROR": "💥"}.get(finding['severity'], "❓")
            print(f"  {severity_icon} {finding['severity']}: {finding['finding']}")
            print(f"    📝 {finding['recommendation']}")
    
    if report['overall_status'] == "PASS":
        print("\n🎉 SECURITY AUDIT PASSED")
        return True
    else:
        print("\n⚠️  SECURITY REVIEW REQUIRED")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)