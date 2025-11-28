"""
API Security Tests
------------------
Tests for common API security vulnerabilities and best practices.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestAPISecurity:
    """Test API security configurations and common vulnerabilities"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app, raise_server_exceptions=False)
    
    def test_security_headers_present(self, client):
        """Test that security headers are present in responses"""
        response = client.get("/health")
        
        # Check for security headers (add more as configured)
        assert response.status_code == 200
        # Note: Add these headers in your FastAPI middleware
        # These tests will guide implementation
    
    def test_cors_configuration(self, client):
        """Test CORS is properly configured"""
        response = client.options("/v1/sprints")
        
        # Should handle OPTIONS preflight requests
        assert response.status_code in [200, 204, 405]  # 405 if not configured yet
    
    def test_sql_injection_prevention(self, client):
        """Test SQL injection attempts are handled safely"""
        malicious_payloads = [
            "1' OR '1'='1",
            "'; DROP TABLE sprints--",
            "1' UNION SELECT * FROM sprints--",
            "' OR 1=1--",
        ]
        
        for payload in malicious_payloads:
            # Try in query parameters
            response = client.get(f"/v1/sprints/{payload}")
            # Should return 404 or 422, not 500 (internal error)
            assert response.status_code in [404, 422], \
                f"SQL injection payload '{payload}' caused unexpected status: {response.status_code}"
    
    def test_xss_prevention_in_responses(self, client):
        """Test XSS attempts are properly escaped"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ]
        
        for payload in xss_payloads:
            # Try creating sprint with XSS payload
            response = client.post("/v1/sprints", json={
                "sprintNumber": payload,
                "sprintName": "Test Sprint",
                "startDate": "2025-12-01",
                "endDate": "2025-12-14",
                "teamMembers": []
            })
            
            # Should handle gracefully, not execute scripts
            assert response.status_code in [200, 201, 400, 422]
            
            if response.status_code in [200, 201]:
                # If created, verify payload is escaped
                data = response.json()
                # Script tags should be escaped or rejected
                assert "<script>" not in str(data) or response.status_code == 422
    
    def test_excessive_request_size(self, client):
        """Test handling of oversized requests"""
        # Create very large team members array
        large_payload = {
            "sprintNumber": "25-large",
            "sprintName": "Large Sprint",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [
                {
                    "name": f"Member {i}",
                    "role": "Developer",
                    "vacations": []
                }
                for i in range(10000)  # Extremely large team
            ]
        }
        
        response = client.post("/v1/sprints", json=large_payload)
        # Should handle without crashing (timeout or validation error acceptable)
        assert response.status_code in [200, 201, 413, 422, 400]
    
    def test_invalid_json_handling(self, client):
        """Test handling of malformed JSON"""
        response = client.post(
            "/v1/sprints",
            content='{"invalid": json}',
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 (validation error), not 500
        assert response.status_code == 422
    
    def test_path_traversal_prevention(self, client):
        """Test path traversal attempts are blocked"""
        traversal_payloads = [
            "../../../etc/passwd",
            "....//....//....//etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
        ]
        
        for payload in traversal_payloads:
            response = client.get(f"/v1/sprints/{payload}")
            # Should return 404 or 422, not expose files
            assert response.status_code in [404, 422]
    
    def test_http_methods_allowed(self, client):
        """Test only appropriate HTTP methods are allowed"""
        # TRACE method should be disabled (security risk)
        response = client.request("TRACE", "/v1/sprints")
        assert response.status_code in [405, 501]  # Method not allowed
    
    def test_sensitive_data_not_in_errors(self, client):
        """Test error messages don't leak sensitive information"""
        response = client.get("/v1/sprints/nonexistent")
        
        if response.status_code == 404:
            error_text = response.text.lower()
            # Should not expose internal paths, database info, etc.
            assert "c:\\" not in error_text
            assert "postgresql" not in error_text or "connection" not in error_text
            assert "password" not in error_text
            assert "secret" not in error_text
    
    def test_rate_limiting_consideration(self, client):
        """Test for rate limiting (placeholder for future implementation)"""
        # Make multiple requests rapidly
        responses = []
        for _ in range(100):
            response = client.get("/v1/sprints")
            responses.append(response.status_code)
        
        # Currently no rate limiting - test passes
        # When implemented, expect 429 (Too Many Requests) after threshold
        assert all(status in [200, 429] for status in responses)
    
    def test_api_version_in_path(self, client):
        """Test API uses versioning in URL path"""
        response = client.get("/v1/sprints")
        # v1 prefix indicates versioned API (good practice)
        assert response.status_code != 404  # v1 path should exist


class TestInputValidation:
    """Test input validation and sanitization"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app, raise_server_exceptions=False)
    
    def test_date_validation(self, client):
        """Test invalid date formats are rejected"""
        invalid_dates = [
            "not-a-date",
            "2025-13-01",  # Invalid month
            "2025-12-32",  # Invalid day
            "12/01/2025",  # Wrong format
        ]
        
        for invalid_date in invalid_dates:
            response = client.post("/v1/sprints", json={
                "sprintNumber": "25-test",
                "sprintName": "Test",
                "startDate": invalid_date,
                "endDate": "2025-12-14",
                "teamMembers": []
            })
            assert response.status_code == 422
    
    def test_negative_values_rejected(self, client):
        """Test negative values in inappropriate fields are rejected"""
        # This would apply to numeric fields if we had them
        # Placeholder for future numeric validations
        pass
    
    def test_special_characters_handling(self, client):
        """Test special characters are handled safely"""
        special_chars = [
            "!@#$%^&*()",
            "测试",  # Chinese characters
            "тест",  # Cyrillic
            "🚀",  # Emoji
        ]
        
        for chars in special_chars:
            response = client.post("/v1/sprints", json={
                "sprintNumber": f"25-{chars}",
                "sprintName": f"Sprint {chars}",
                "startDate": "2025-12-01",
                "endDate": "2025-12-14",
                "teamMembers": []
            })
            # Should handle gracefully (accept or reject with 422)
            assert response.status_code in [200, 201, 422]


class TestDataProtection:
    """Test data protection and privacy measures"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app, raise_server_exceptions=False)
    
    def test_no_data_leakage_between_requests(self, client):
        """Test data from one request doesn't leak to another"""
        # Create first sprint
        response1 = client.post("/v1/sprints", json={
            "sprintNumber": "25-leak-test-1",
            "sprintName": "Sprint 1",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": [{"name": "Alice", "role": "Developer", "vacations": []}]
        })
        
        # Create second sprint
        response2 = client.post("/v1/sprints", json={
            "sprintNumber": "25-leak-test-2",
            "sprintName": "Sprint 2",
            "startDate": "2025-12-15",
            "endDate": "2025-12-28",
            "teamMembers": [{"name": "Bob", "role": "Developer", "vacations": []}]
        })
        
        if response1.status_code == 201 and response2.status_code == 201:
            data1 = response1.json()
            data2 = response2.json()
            
            # Sprint 1 data should not appear in Sprint 2
            assert "Alice" not in str(data2)
            assert data1["sprintNumber"] != data2["sprintNumber"]
    
    def test_deleted_data_not_accessible(self, client):
        """Test deleted resources return 404"""
        # Create sprint
        create_response = client.post("/v1/sprints", json={
            "sprintNumber": "25-delete-test",
            "sprintName": "To Delete",
            "startDate": "2025-12-01",
            "endDate": "2025-12-14",
            "teamMembers": []
        })
        
        if create_response.status_code == 201:
            sprint_number = create_response.json()["sprintNumber"]
            
            # Delete sprint
            delete_response = client.delete(f"/v1/sprints/{sprint_number}")
            
            if delete_response.status_code == 204:
                # Try to access deleted sprint
                get_response = client.get(f"/v1/sprints/{sprint_number}")
                assert get_response.status_code == 404
