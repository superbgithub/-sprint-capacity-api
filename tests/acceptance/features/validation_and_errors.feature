Feature: Data Validation and Error Handling
  As an API consumer
  I want proper validation and error messages
  So that I can understand and fix issues with my requests

  Background:
    Given the API is running

  Scenario: Missing required field - sprint number
    When I create a sprint without a sprint number
    Then the request should fail with status code 422
    And the error should indicate "sprintNumber" is required

  Scenario: Missing required field - start date
    When I create a sprint without a start date
    Then the request should fail with status code 422
    And the error should indicate "startDate" is required

  Scenario: Invalid date format
    When I create a sprint with start date "invalid-date"
    Then the request should fail with status code 422
    And the error should indicate invalid date format

  Scenario: Confidence percentage out of range
    When I create a sprint with confidence percentage -10.0
    Then the request should fail with status code 422
    And the error should indicate confidence must be between 0 and 100

  Scenario: Sprint number too long
    When I create a sprint with sprint number "25-12345678901"
    Then the request should fail with status code 422
    And the error should indicate sprint number exceeds maximum length

  Scenario: Team member without name
    When I create a sprint with a team member missing a name
    Then the request should fail with status code 422
    And the error should indicate team member name is required

  Scenario: Invalid vacation dates
    When I create a sprint with vacation end date before start date
    Then the request should fail with status code 422
    And the error should indicate invalid vacation date range

  Scenario: Holiday without date
    When I create a sprint with a holiday missing the date field
    Then the request should fail with status code 422
    And the error should indicate holiday date is required

  Scenario Outline: Invalid confidence percentages
    When I create a sprint with confidence percentage <value>
    Then the request should fail with status code 422
    And the error should indicate confidence must be between 0 and 100

    Examples:
      | value  |
      | -1.0   |
      | 101.0  |
      | 150.0  |
      | -50.0  |

  Scenario: Empty team members array
    Given I have sprint data with an empty team members array
    When I create the sprint
    Then the sprint should be created successfully
    And the sprint should have 0 team members

  Scenario: Extremely long string in text field
    When I create a sprint with a 10000 character holiday name
    Then the request should fail with status code 422 or 500
    And the error should indicate field length exceeded

  Scenario: Special characters in sprint number
    When I create a sprint with sprint number "25-@#$%"
    Then the request should fail with status code 422
    And the error should indicate invalid characters

  Scenario: Update non-existent sprint
    When I update a sprint with ID "non-existent-12345"
    Then the request should fail with status code 404
    And the error should indicate sprint not found

  Scenario: Delete already deleted sprint
    Given a sprint exists with sprint number "25-701"
    And the sprint has been deleted
    When I try to delete the sprint again
    Then the request should fail with status code 404
