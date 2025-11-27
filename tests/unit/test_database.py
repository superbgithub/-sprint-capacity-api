"""
Unit tests for database operations.
NOTE: These tests are currently skipped because they need to be updated for async PostgreSQL.
The database now uses async/await and requires a running PostgreSQL instance.
Use integration tests or functional tests instead, or update these to use pytest-asyncio.
"""
import pytest
from datetime import date, datetime
from app.services.database import Database
from app.models.schemas import SprintInput, TeamMemberInput, RoleEnum


@pytest.mark.skip(reason="Database tests need async/PostgreSQL setup - use functional tests instead")
class TestDatabase:
    """Test database operations"""
    
    @pytest.fixture
    def db(self):
        """Create fresh database for each test"""
        return Database()
    
    @pytest.fixture
    def sample_sprint_input(self):
        """Sample sprint data"""
        return SprintInput(
            sprintNumber="25-01",
            startDate=date(2025, 11, 26),
            endDate=date(2025, 12, 9),
            confidencePercentage=85.0,
            teamMembers=[
                TeamMemberInput(
                    name="John Doe",
                    role=RoleEnum.DEVELOPER,
                    vacations=[]
                )
            ],
            holidays=[]
        )
    
    def test_create_sprint(self, db, sample_sprint_input):
        """Test creating a sprint"""
        sprint = db.create_sprint(sample_sprint_input)
        
        assert sprint.id is not None
        assert sprint.id.startswith("sprint-")
        assert sprint.sprintNumber == "25-01"
        assert sprint.sprintName == "Sprint 25-01"
        assert sprint.sprintDuration >= 1  # Auto-calculated working days
        assert sprint.confidencePercentage == 85.0
        assert len(sprint.teamMembers) == 1
        assert sprint.createdAt is not None
        assert sprint.updatedAt is not None
    
    def test_create_sprint_generates_ids(self, db, sample_sprint_input):
        """Test that IDs are generated for all entities"""
        sprint = db.create_sprint(sample_sprint_input)
        
        # Check team member ID
        assert sprint.teamMembers[0].id.startswith("tm-")
    
    def test_get_sprint(self, db, sample_sprint_input):
        """Test retrieving a sprint by ID"""
        created = db.create_sprint(sample_sprint_input)
        retrieved = db.get_sprint(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.sprintNumber == created.sprintNumber
        assert retrieved.sprintName == created.sprintName
    
    def test_get_sprint_not_found(self, db):
        """Test retrieving non-existent sprint"""
        result = db.get_sprint("non-existent-id")
        assert result is None
    
    def test_get_all_sprints(self, db, sample_sprint_input):
        """Test retrieving all sprints"""
        sprint1 = db.create_sprint(sample_sprint_input)
        sprint2 = db.create_sprint(sample_sprint_input)
        
        all_sprints = db.get_all_sprints()
        
        assert len(all_sprints) == 2
        assert sprint1.id in [s.id for s in all_sprints]
        assert sprint2.id in [s.id for s in all_sprints]
    
    def test_update_sprint(self, db, sample_sprint_input):
        """Test updating a sprint"""
        created = db.create_sprint(sample_sprint_input)
        
        # Update data
        update_data = SprintInput(
            sprintNumber="25-02",
            confidencePercentage=90.0,
            startDate=date(2025, 12, 1),
            endDate=date(2025, 12, 10),
            teamMembers=[
                TeamMemberInput(
                    name="Jane Smith",
                    role=RoleEnum.TESTER,
                    vacations=[]
                )
            ],
            holidays=[]
        )
        
        updated = db.update_sprint(created.id, update_data)
        
        assert updated is not None
        assert updated.id == created.id
        assert updated.sprintNumber == "25-02"
        assert updated.sprintName == "Sprint 25-02"
        assert updated.sprintDuration >= 1  # Auto-calculated
        assert updated.confidencePercentage == 90.0
        assert updated.createdAt == created.createdAt  # Should not change
        assert updated.updatedAt > created.updatedAt  # Should be newer
    
    def test_update_sprint_not_found(self, db, sample_sprint_input):
        """Test updating non-existent sprint"""
        result = db.update_sprint("non-existent-id", sample_sprint_input)
        assert result is None
    
    def test_delete_sprint(self, db, sample_sprint_input):
        """Test deleting a sprint"""
        created = db.create_sprint(sample_sprint_input)
        
        success = db.delete_sprint(created.id)
        assert success is True
        
        # Verify it's deleted
        retrieved = db.get_sprint(created.id)
        assert retrieved is None
    
    def test_delete_sprint_not_found(self, db):
        """Test deleting non-existent sprint"""
        success = db.delete_sprint("non-existent-id")
        assert success is False
    
    def test_generate_id(self, db):
        """Test ID generation"""
        id1 = db.generate_id("test")
        id2 = db.generate_id("test")
        
        assert id1.startswith("test-")
        assert id2.startswith("test-")
        assert id1 != id2  # Should be unique
