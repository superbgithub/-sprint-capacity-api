Feature: Capacity Calculation
  As a scrum master
  I want to calculate team capacity for a sprint
  So that I can understand available working days

  Background:
    Given the API is running
    And the database is clean

  Scenario: Calculate capacity for sprint with no vacations or holidays
    Given a sprint exists from "2025-12-01" to "2025-12-14" with 3 team members
    When I request the capacity calculation
    Then the total capacity should be 30 days
    And each team member should have 10 working days

  Scenario: Calculate capacity excluding weekends
    Given a sprint runs from Monday "2025-12-01" to Sunday "2025-12-14"
    And the sprint has 2 team members
    When I request the capacity calculation
    Then weekends should be excluded from capacity
    And the total capacity should be 20 days

  Scenario: Calculate capacity with team member vacations
    Given a sprint exists from "2025-12-01" to "2025-12-14" with 2 team members
    And one team member has vacation from "2025-12-05" to "2025-12-06"
    When I request the capacity calculation
    Then the total capacity should be 19 days

  Scenario: Calculate capacity with holidays
    Given a sprint exists from "2025-12-01" to "2025-12-14" with 3 team members
    And the sprint has a holiday on "2025-12-10"
    When I request the capacity calculation
    Then each team member should have 9 working days
    And the total capacity should be 27 days

  Scenario: Calculate capacity with both vacations and holidays
    Given a sprint exists from "2025-12-01" to "2025-12-20" with 3 team members
    And one team member has vacation from "2025-12-08" to "2025-12-09"
    And the sprint has a holiday on "2025-12-10"
    When I request the capacity calculation
    Then the total capacity should be correctly calculated

  Scenario: Calculate capacity for sprint with confidence percentage
    Given a sprint exists with confidence percentage 80.0
    And the sprint has calculated capacity of 30 days
    When I request the capacity calculation
    Then the response should include confidence percentage
    And the confidence percentage should be 80.0

  Scenario: Handle capacity calculation for deleted sprint
    When I request capacity for a non-existent sprint ID
    Then the request should fail with status code 404

  Scenario: Capacity calculation with overlapping vacations
    Given a sprint exists from "2025-12-01" to "2025-12-14"
    And a team member has vacation from "2025-12-05" to "2025-12-10"
    And the same team member has vacation from "2025-12-08" to "2025-12-12"
    When I request the capacity calculation
    Then overlapping vacation days should not be counted twice
    And the capacity should be correctly calculated

  Scenario: Multi-day holiday affects all team members
    Given a sprint exists from "2025-12-01" to "2025-12-14"
    And the sprint has 5 team members
    And the sprint has holidays on "2025-12-10" and "2025-12-11"
    When I request the capacity calculation
    Then all team members should lose 2 working days
    And the total capacity should be 40 days

  Scenario: Vacation spanning entire sprint
    Given a sprint exists from "2025-12-01" to "2025-12-14"
    And a team member has vacation covering the entire sprint period
    When I request the capacity calculation
    Then that team member's capacity should be 0 days
