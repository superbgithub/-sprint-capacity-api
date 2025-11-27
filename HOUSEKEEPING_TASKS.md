# Housekeeping Tasks - Sprint Capacity API

## 1. Test Fixtures Need Schema Updates (17 failing tests) 🔴 HIGH PRIORITY

### Files to Update:

#### `tests/unit/test_capacity_service.py` (5 failures)
**Issue**: Tests use old schema with `sprintName` and `sprintDuration` as inputs

**Current (WRONG)**:
```python
sprint = Sprint(
    id='test-sprint',
    sprintName='Test Sprint',
    sprintDuration=14,  # ❌ Should not be input
    startDate=date(2025, 1, 1),
    endDate=date(2025, 1, 14),
    teamMembers=[...],
    holidays=[]
)
```

**Should Be**:
```python
sprint = Sprint(
    id='test-sprint',
    sprintNumber='25-01',  # ✅ New field
    sprintName='Sprint 25-01',  # ✅ Auto-generated
    sprintDuration=10,  # ✅ Auto-calculated (not input)
    confidencePercentage=85.0,  # ✅ Sprint-level
    startDate=date(2025, 1, 1),
    endDate=date(2025, 1, 14),
    teamMembers=[...],  # ❌ Remove confidencePercentage from team members
    holidays=[]
)
```

**Tests Failing**:
- `test_single_member_no_vacation`
- `test_single_member_with_confidence`
- `test_multiple_members`
- `test_member_with_vacation`
- `test_sprint_with_holiday`

---

#### `tests/functional/test_workflows.py` (5 failures)
**Issue**: Uses old API request format

**Current (WRONG)**:
```python
sprint_data = {
    "sprintName": "Test Sprint",  # ❌ Old field
    "sprintDuration": 14,  # ❌ Should not be input
    "startDate": "2025-01-01",
    "endDate": "2025-01-14",
    "teamMembers": [
        {
            "name": "John Doe",
            "role": "Developer",
            "confidencePercentage": 85.0,  # ❌ No longer on team member
            "vacations": []
        }
    ]
}
```

**Should Be**:
```python
sprint_data = {
    "sprintNumber": "25-01",  # ✅ New format
    "startDate": "2025-01-01",
    "endDate": "2025-01-14",
    "confidencePercentage": 85.0,  # ✅ Sprint-level
    "teamMembers": [
        {
            "name": "John Doe",
            "role": "Developer",
            "vacations": []
        }
    ],
    "holidays": []
}
```

**Tests Failing**:
- `test_complete_sprint_workflow`
- `test_create_multiple_sprints_and_manage`
- `test_capacity_with_holidays_and_vacations`
- `test_invalid_data_recovery_workflow`
- `test_not_found_error_handling`

---

#### `tests/contract/test_api_contracts.py` (7 failures)
**Issue**: API contract tests expect old response schema

**Current (WRONG)**:
```python
# Expects response with sprintName, sprintDuration as inputs
assert "sprintName" in response  # ❌ Still exists but auto-generated
assert "sprintDuration" in response  # ❌ Auto-calculated, not input
```

**Should Be**:
```python
assert "sprintNumber" in response  # ✅ New field
assert "sprintName" in response  # ✅ Still exists (auto-generated)
assert "sprintDuration" in response  # ✅ Still exists (auto-calculated)
assert "confidencePercentage" in response  # ✅ Sprint-level
```

**Tests Failing**:
- `test_create_sprint_request_schema`
- `test_get_sprint_by_id_response_schema`
- `test_get_sprint_not_found`
- `test_get_capacity_response_schema`
- `test_update_sprint_response_schema`
- `test_delete_sprint_response`

---

## 2. Pydantic V2 Deprecation Warnings (12 warnings) 🟡 MEDIUM PRIORITY

### File: `app/models/schemas.py`

**Issue**: Using deprecated `class Config:` instead of `ConfigDict`

**Current (WRONG)**:
```python
class VacationInput(BaseModel):
    startDate: date = Field(...)
    endDate: date = Field(...)
    
    class Config:  # ❌ Deprecated in Pydantic V2
        json_schema_extra = {"example": {...}}
```

**Should Be**:
```python
from pydantic import BaseModel, Field, ConfigDict

class VacationInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {...}}
    )
    
    startDate: date = Field(...)
    endDate: date = Field(...)
```

**Classes to Update** (12 total):
1. `VacationInput` (line 21)
2. `Vacation` (line 37)
3. `TeamMemberBase` (line 54)
4. `SprintAssignmentInput` (line 73)
5. `TeamMemberInput` (line 92)
6. `TeamMember` (line 111)
7. `HolidayInput` (line 130)
8. `Holiday` (line 146)
9. `SprintInput` (line 161)
10. `Sprint` (line 196)
11. `CapacitySummary` (line 236)
12. `ErrorResponse` (line 264)

---

## 3. Kafka Event Publishing Not Working 🟢 LOW PRIORITY

### File: `app/events/kafka_producer.py`

**Issue**: Producer fails to initialize, falls back to logging

**Current Behavior**:
```
Kafka disabled. Would publish to sprint.lifecycle: {...}
```

**What's Wrong**:
- Producer initialization fails
- Events are logged but not published to Kafka
- Graceful degradation is working (no errors)

**To Fix**:
1. Check Kafka bootstrap server connection
2. Verify Kafka container networking
3. Test producer initialization
4. Enable event publishing

**Why It's Low Priority**:
- System works without it (graceful degradation)
- Events are logged for debugging
- Not critical for core functionality

---

## 4. Frontend Server Not Staying Running 🟢 LOW PRIORITY

**Issue**: Frontend starts but doesn't stay running

**What Happened**:
```
Compiled successfully!
You can now view team-capacity-frontend in the browser.
  Local:            http://localhost:3001

[Process exits immediately]
```

**Why It's Low Priority**:
- Frontend code is updated and compiles successfully
- Can be started manually when needed
- Not part of Docker stack
- Dev environment only

---

## Summary Table

| Task | Priority | Files | Effort | Impact |
|------|----------|-------|--------|--------|
| Fix test fixtures | 🔴 HIGH | 3 files, 17 tests | 1-2 hours | CI/CD will fail |
| Pydantic warnings | 🟡 MEDIUM | 1 file, 12 classes | 30 mins | Warnings only |
| Kafka publishing | 🟢 LOW | 1 file | 1 hour | Non-critical |
| Frontend server | 🟢 LOW | - | - | Dev only |

---

## Quick Fix Commands

### Run Tests to See Failures:
```bash
pytest tests/unit/test_capacity_service.py -v
pytest tests/functional/test_workflows.py -v
pytest tests/contract/test_api_contracts.py -v
```

### Check Pydantic Warnings:
```bash
pytest tests/ -v 2>&1 | grep "PydanticDeprecatedSince20"
```

### Test Kafka Connection:
```bash
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

---

## Recommendation

**Start with HIGH priority** (test fixtures):
1. Update `test_capacity_service.py` first (easiest)
2. Update `test_workflows.py` second
3. Update `test_api_contracts.py` last

Then CI/CD will pass! The other items are nice-to-have.
