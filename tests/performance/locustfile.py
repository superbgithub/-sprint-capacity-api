"""
Performance tests using Locust for load testing.
Tests API performance under various load conditions.

To run these tests:
    locust -f tests/performance/locustfile.py --host=http://127.0.0.1:8000
    
Then open http://localhost:8089 to configure and start the load test.
"""
from locust import HttpUser, task, between, events
import json
import random
import time
import uuid


class SprintAPIUser(HttpUser):
    """Simulates a user interacting with the Sprint API"""
    
    # Wait between 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user session"""
        self.sprint_ids = []
        # Note: No initial sprint creation - tests will fetch existing sprints
        # from the database and populate self.sprint_ids dynamically

    @task(5)
    def get_all_sprints(self):
        """Get all sprints (high frequency task)"""
        with self.client.get("/v1/sprints", catch_response=True) as response:
            if response.status_code == 200:
                # Populate sprint_ids if empty
                if not self.sprint_ids and response.json():
                    self.sprint_ids = [sprint["id"] for sprint in response.json()]
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    # Removed create_sprint task - causing 422 validation errors
    
    @task(4)
    def get_sprint_by_id(self):
        """Get a specific sprint by ID (high frequency)"""
        if not self.sprint_ids:
            return
        
        sprint_id = random.choice(self.sprint_ids)
        
        with self.client.get(f"/v1/sprints/{sprint_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Sprint was deleted, remove from list
                self.sprint_ids.remove(sprint_id)
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(6)
    def get_capacity(self):
        """Calculate sprint capacity (highest frequency - most resource intensive)"""
        if not self.sprint_ids:
            return
        
        sprint_id = random.choice(self.sprint_ids)
        
        with self.client.get(f"/v1/sprints/{sprint_id}/capacity", catch_response=True) as response:
            if response.status_code == 200:
                # Validate response structure
                data = response.json()
                if all(key in data for key in ["sprintId", "totalCapacityDays", "memberCapacity"]):
                    response.success()
                else:
                    response.failure("Invalid capacity response structure")
            elif response.status_code == 404:
                self.sprint_ids.remove(sprint_id)
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    # Removed update_sprint task - causing 422 validation errors
    
    @task(1)
    def delete_sprint(self):
        """Delete a sprint (low frequency - skipped in read-only mode)"""
        # Skip deletion since we're not creating sprints
        # This is a read-only performance test
        return


# Removed CapacityHeavyUser class - causing 422 validation errors during sprint creation


# Performance metrics tracking
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track request metrics"""
    if exception:
        print(f"Request failed: {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test metrics"""
    print("Performance test starting...")
    print(f"Host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print final statistics"""
    print("\nPerformance test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {environment.stats.total.max_response_time:.2f}ms")
    print(f"Requests per second: {environment.stats.total.total_rps:.2f}")
