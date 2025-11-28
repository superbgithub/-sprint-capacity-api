# Security Tests

This directory contains comprehensive security tests for the Sprint Capacity API.

## Test Categories

### 1. API Security Tests (`test_api_security.py`)

Tests for common API security vulnerabilities and best practices:

- **Security Headers**: Validates presence of security headers (X-Content-Type-Options, X-Frame-Options, etc.)
- **CORS Configuration**: Tests Cross-Origin Resource Sharing configuration
- **SQL Injection Prevention**: Tests SQL injection attempts are handled safely
- **XSS Prevention**: Tests cross-site scripting attempts are properly escaped
- **Request Size Limits**: Tests handling of oversized requests
- **Invalid JSON Handling**: Tests malformed JSON is rejected gracefully
- **Path Traversal Prevention**: Tests directory traversal attempts are blocked
- **HTTP Method Restrictions**: Tests only appropriate HTTP methods are allowed
- **Error Message Security**: Tests error messages don't leak sensitive information
- **Rate Limiting**: Placeholder for rate limiting implementation
- **API Versioning**: Tests API uses versioning in URL path

### 2. Input Validation Tests

Tests for input validation and sanitization:

- **Date Validation**: Tests invalid date formats are rejected
- **Special Characters**: Tests special characters (Unicode, emoji) are handled safely
- **Negative Values**: Tests inappropriate negative values are rejected

### 3. Data Protection Tests

Tests for data protection and privacy:

- **Data Isolation**: Tests data from one request doesn't leak to another
- **Deletion Verification**: Tests deleted resources are truly inaccessible

### 4. Dependency Security Tests (`test_dependency_security.py`)

Tests for vulnerabilities in third-party dependencies:

- **Safety Check**: Uses `safety` to check against known vulnerability database
- **Pip-Audit Check**: Alternative security check using `pip-audit`
- **Secret Scanning**: Basic check for hardcoded secrets in code

## Security Tools Used

### Static Analysis (SAST)
- **Bandit**: Python security linter that finds common security issues
  - Scans for: SQL injection, hardcoded passwords, weak crypto, etc.
  - Severity levels: Low, Medium, High

### Dependency Scanning
- **Safety**: Checks Python dependencies against known security advisories
  - Database: PyUp.io safety database
  - Checks: Known CVEs in packages

- **pip-audit**: Audits Python packages for known vulnerabilities
  - Database: OSV (Open Source Vulnerabilities) and PyPI
  - More comprehensive than safety

### Dynamic Testing
- **pytest**: Runtime security tests against live API
  - Tests actual application behavior
  - Validates security configurations

## Running Security Tests Locally

### Run all security tests:
```bash
pytest tests/security/ -v
```

### Run specific test categories:
```bash
# API security tests only
pytest tests/security/test_api_security.py -v

# Dependency security tests only
pytest tests/security/test_dependency_security.py -v
```

### Run security scans manually:

#### Bandit (Static Analysis):
```bash
# Scan with default settings
bandit -r app/

# Show only high severity issues
bandit -r app/ -ll

# Generate JSON report
bandit -r app/ -f json -o bandit-report.json
```

#### Safety (Dependency Check):
```bash
# Check for vulnerabilities
safety check

# Generate JSON report
safety check --json --output safety-report.json

# Check specific requirements file
safety check -r requirements.txt
```

#### Pip-Audit (Dependency Audit):
```bash
# Audit installed packages
pip-audit

# Generate JSON report
pip-audit --format json --output pip-audit-report.json

# Audit from requirements file
pip-audit -r requirements.txt
```

## CI/CD Integration

Security tests run as **Stage 7** in the CI/CD pipeline, after resiliency tests and before acceptance tests.

The security stage includes:
1. **Bandit SAST scan** - Static code analysis for security issues
2. **Safety check** - Dependency vulnerability scanning
3. **Pip-audit check** - Additional dependency security audit
4. **Pytest security tests** - Runtime security validation

All security reports are uploaded as artifacts for review.

## Security Test Results

### Expected Behavior

✅ **Pass**: Secure implementation detected
- Proper input validation
- SQL injection prevented via parameterized queries
- XSS attempts properly escaped
- No known vulnerabilities in dependencies

⚠️ **Warning**: Potential improvement area
- Security headers not configured (implement middleware)
- Rate limiting not implemented (future enhancement)
- Some tests may be skipped if tools not available

❌ **Fail**: Security issue detected
- Known CVE in dependency (upgrade package)
- Hardcoded secrets found (use environment variables)
- SQL injection vulnerability detected
- XSS vulnerability detected

## Security Best Practices

### Code Level
- ✅ Use parameterized queries (SQLAlchemy ORM)
- ✅ Validate all inputs with Pydantic models
- ✅ Use async/await for database operations
- ⚠️ TODO: Add security headers middleware
- ⚠️ TODO: Implement rate limiting
- ⚠️ TODO: Add authentication/authorization

### Dependency Management
- ✅ Pin exact versions in requirements.txt
- ✅ Regular security scans in CI/CD
- ⚠️ TODO: Set up automated dependency updates (Dependabot)
- ⚠️ TODO: Regular manual review of security advisories

### Configuration
- ✅ Use environment variables for sensitive data
- ✅ No hardcoded credentials
- ✅ Separate test/production databases
- ⚠️ TODO: Implement secrets management (AWS Secrets Manager, Vault)
- ⚠️ TODO: Add HTTPS enforcement in production

## Integrating with Security Tools

### GitHub Security Features
Enable these in your repository:
- **Dependabot**: Automated dependency updates
- **Code Scanning**: GitHub Advanced Security (if available)
- **Secret Scanning**: Detect committed secrets

### Additional Tools to Consider
- **OWASP ZAP**: Dynamic application security testing
- **SonarQube**: Code quality and security analysis
- **Snyk**: Continuous security monitoring
- **TruffleHog**: Git secrets scanning
- **detect-secrets**: Pre-commit hook for secrets

## Security Incident Response

If security tests fail:

1. **Review the report**: Check which tests failed and why
2. **Assess severity**: High severity issues require immediate attention
3. **Investigate**: Understand the vulnerability details
4. **Fix**: Apply patches, upgrade dependencies, or fix code
5. **Verify**: Re-run security tests to confirm fix
6. **Document**: Record incident and remediation steps

## Compliance Considerations

These tests help with:
- **OWASP Top 10**: Coverage for common vulnerabilities
- **CWE/SANS Top 25**: Most dangerous software weaknesses
- **GDPR**: Data protection and privacy (partial coverage)
- **SOC 2**: Security controls and monitoring

## Contributing

When adding new features:
1. Consider security implications
2. Add appropriate security tests
3. Run security scans locally before committing
4. Review security test results in CI/CD

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://pyup.io/safety/)
- [pip-audit Documentation](https://pypi.org/project/pip-audit/)
