Feature: Sprint Management
  As a scrum master
  I want to manage sprint information
  So that I can track and plan team capacity

  Background:
    Given the API is running
    And the database is clean

  Scenario: Create a new sprint with valid data
    Given I have valid sprint data with sprint number "25-101"
    When I create a new sprint
    Then the sprint should be created successfully
    And the response should contain the sprint ID
    And the sprint number should be "25-101"

  Scenario: Create sprint with team members
    Given I have sprint data with the following team members:
      | name          | role      |
      | Alice Smith   | Developer |
      | Bob Johnson   | Tester    |
      | Carol Wilson  | Manager   |
    When I create a new sprint with sprint number "25-102"
    Then the sprint should be created successfully
    And the sprint should have 3 team members

  Scenario: Cannot create sprint with duplicate sprint number
    Given a sprint exists with sprint number "25-103"
    When I try to create another sprint with sprint number "25-103"
    Then the request should fail with status code 422
    And the error message should indicate duplicate sprint number

  Scenario: Retrieve all sprints
    Given the following sprints exist:
      | sprintNumber | startDate  | endDate    |
      | 25-201       | 2025-12-01 | 2025-12-14 |
      | 25-202       | 2025-12-15 | 2025-12-28 |
      | 25-203       | 2026-01-05 | 2026-01-18 |
    When I request all sprints
    Then I should receive 3 sprints
    And the sprints should be in the response

  Scenario: Retrieve a specific sprint by ID
    Given a sprint exists with sprint number "25-301"
    When I request the sprint by its ID
    Then the sprint details should be returned
    And the sprint number should be "25-301"

  Scenario: Update sprint information
    Given a sprint exists with sprint number "25-401"
    When I update the sprint with new data:
      | field               | value      |
      | startDate           | 2026-02-01 |
      | endDate             | 2026-02-14 |
      | confidencePercentage| 85.5       |
    Then the sprint should be updated successfully
    And the updated fields should be reflected

  Scenario: Delete a sprint
    Given a sprint exists with sprint number "25-501"
    When I delete the sprint
    Then the sprint should be deleted successfully
    And requesting the sprint should return 404

  Scenario: Cannot retrieve non-existent sprint
    When I request a sprint with ID "non-existent-id"
    Then the request should fail with status code 404

  Scenario: Validate sprint number format
    When I try to create a sprint with sprint number "invalid-format-123456789"
    Then the request should fail with status code 422
    And the error message should indicate invalid sprint number format

  Scenario: Sprint date validation
    When I try to create a sprint where end date is before start date
    Then the request should fail with status code 422
    And the error message should indicate invalid date range
