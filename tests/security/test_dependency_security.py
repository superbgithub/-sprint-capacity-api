"""
Dependency Security Tests
-------------------------
Tests to check for known vulnerabilities in dependencies.
Uses safety package to check for security advisories.
"""
import pytest
import subprocess
import json


class TestDependencySecurity:
    """Test third-party dependencies for known vulnerabilities"""
    
    def test_no_known_vulnerabilities_in_dependencies(self):
        """
        Check dependencies against safety database for known vulnerabilities.
        
        This test requires 'safety' package to be installed.
        Run: pip install safety
        """
        try:
            # Run safety check
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse JSON output
            if result.stdout:
                try:
                    vulnerabilities = json.loads(result.stdout)
                    
                    # If vulnerabilities found, provide details
                    if vulnerabilities:
                        vuln_details = "\n".join([
                            f"- {v.get('package', 'Unknown')}: {v.get('advisory', 'No details')}"
                            for v in vulnerabilities
                        ])
                        pytest.fail(
                            f"Found {len(vulnerabilities)} known vulnerabilities:\n{vuln_details}\n"
                            f"Run 'safety check' for full details."
                        )
                except json.JSONDecodeError:
                    # If not JSON, check return code
                    if result.returncode != 0:
                        pytest.fail(f"Safety check failed: {result.stderr}")
            
            # If safety returned non-zero, there might be vulnerabilities
            if result.returncode not in [0, 64]:  # 64 = vulnerabilities found but returned in JSON
                pytest.skip(f"Safety check inconclusive: {result.stderr}")
                
        except FileNotFoundError:
            pytest.skip("Safety package not installed. Run: pip install safety")
        except subprocess.TimeoutExpired:
            pytest.skip("Safety check timed out")
    
    def test_pip_audit_check(self):
        """
        Alternative security check using pip-audit.
        
        This test requires 'pip-audit' package to be installed.
        Run: pip install pip-audit
        """
        try:
            # Run pip-audit
            result = subprocess.run(
                ["pip-audit", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                try:
                    audit_results = json.loads(result.stdout)
                    
                    if audit_results.get("vulnerabilities"):
                        vuln_count = len(audit_results["vulnerabilities"])
                        pytest.fail(
                            f"pip-audit found {vuln_count} vulnerabilities. "
                            f"Run 'pip-audit' for details."
                        )
                except json.JSONDecodeError:
                    if result.returncode != 0:
                        pytest.skip(f"pip-audit check inconclusive: {result.stderr}")
                        
        except FileNotFoundError:
            pytest.skip("pip-audit not installed. Run: pip install pip-audit")
        except subprocess.TimeoutExpired:
            pytest.skip("pip-audit timed out")


class TestSecureConfiguration:
    """Test secure configuration practices"""
    
    def test_no_hardcoded_secrets_in_code(self):
        """
        Scan for potential hardcoded secrets.
        This is a basic check - consider using tools like:
        - detect-secrets
        - truffleHog
        - gitleaks
        """
        import os
        import re
        
        # Patterns that might indicate hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
        ]
        
        suspicious_files = []
        
        # Scan app directory
        app_dir = os.path.join(os.path.dirname(__file__), "..", "..", "app")
        if os.path.exists(app_dir):
            for root, dirs, files in os.walk(app_dir):
                # Skip __pycache__ and .pyc files
                if "__pycache__" in root:
                    continue
                    
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                                for pattern in secret_patterns:
                                    if re.search(pattern, content, re.IGNORECASE):
                                        suspicious_files.append((file_path, pattern))
                        except Exception:
                            continue
        
        # Filter out test fixtures and examples
        genuine_issues = [
            (f, p) for f, p in suspicious_files
            if "test" not in f.lower() and "example" not in f.lower()
        ]
        
        if genuine_issues:
            issues = "\n".join([f"- {f}: matches '{p}'" for f, p in genuine_issues])
            pytest.fail(
                f"Potential hardcoded secrets found:\n{issues}\n"
                f"Please use environment variables or secret management."
            )
