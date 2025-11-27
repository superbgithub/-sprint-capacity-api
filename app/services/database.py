"""
In-memory database for the POC.
For production, replace this with a real database (PostgreSQL, MongoDB, etc.)
"""
from typing import Dict, List, Optional
from datetime import datetime
from app.models.schemas import Sprint, SprintInput, TeamMember, Vacation, Holiday
import uuid


class Database:
    """Simple in-memory database using dictionaries"""
    
    def __init__(self):
        self.sprints: Dict[str, Sprint] = {}
    
    def generate_id(self, prefix: str = "sprint") -> str:
        """Generate a unique ID with a prefix"""
        return f"{prefix}-{uuid.uuid4().hex[:8]}"
    
    def create_sprint(self, sprint_input: SprintInput) -> Sprint:
        """
        Create a new sprint with generated IDs for sprint, team members, holidays, and vacations.
        
        Args:
            sprint_input: Sprint input data
        
        Returns:
            Created sprint with all IDs assigned
        """
        sprint_id = self.generate_id("sprint")
        
        # Process team members and assign IDs
        team_members = []
        for tm_input in sprint_input.teamMembers:
            member_id = self.generate_id("tm")
            
            # Process vacations and assign IDs
            vacations = []
            if tm_input.vacations:
                for vac_input in tm_input.vacations:
                    vacation_id = self.generate_id("vac")
                    vacation = Vacation(
                        id=vacation_id,
                        startDate=vac_input.startDate,
                        endDate=vac_input.endDate,
                        reason=vac_input.reason,
                        daysCount=None  # Will be calculated by capacity service
                    )
                    vacations.append(vacation)
            
            team_member = TeamMember(
                id=member_id,
                name=tm_input.name,
                role=tm_input.role,
                confidencePercentage=tm_input.confidencePercentage,
                vacations=vacations
            )
            team_members.append(team_member)
        
        # Process holidays and assign IDs
        holidays = []
        if sprint_input.holidays:
            for hol_input in sprint_input.holidays:
                holiday_id = self.generate_id("holiday")
                holiday = Holiday(
                    id=holiday_id,
                    holidayDate=hol_input.holidayDate,
                    name=hol_input.name,
                    description=hol_input.description
                )
                holidays.append(holiday)
        
        # Create the sprint
        sprint = Sprint(
            id=sprint_id,
            sprintName=sprint_input.sprintName,
            sprintDuration=sprint_input.sprintDuration,
            startDate=sprint_input.startDate,
            endDate=sprint_input.endDate,
            teamMembers=team_members,
            holidays=holidays,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        
        self.sprints[sprint_id] = sprint
        return sprint
    
    def get_sprint(self, sprint_id: str) -> Optional[Sprint]:
        """Get a sprint by ID"""
        return self.sprints.get(sprint_id)
    
    def get_all_sprints(self) -> List[Sprint]:
        """Get all sprints"""
        return list(self.sprints.values())
    
    def update_sprint(self, sprint_id: str, sprint_input: SprintInput) -> Optional[Sprint]:
        """
        Update an existing sprint.
        
        Args:
            sprint_id: ID of sprint to update
            sprint_input: New sprint data
        
        Returns:
            Updated sprint or None if not found
        """
        if sprint_id not in self.sprints:
            return None
        
        old_sprint = self.sprints[sprint_id]
        
        # Process team members (similar to create)
        team_members = []
        for tm_input in sprint_input.teamMembers:
            member_id = self.generate_id("tm")
            
            vacations = []
            if tm_input.vacations:
                for vac_input in tm_input.vacations:
                    vacation_id = self.generate_id("vac")
                    vacation = Vacation(
                        id=vacation_id,
                        startDate=vac_input.startDate,
                        endDate=vac_input.endDate,
                        reason=vac_input.reason,
                        daysCount=None
                    )
                    vacations.append(vacation)
            
            team_member = TeamMember(
                id=member_id,
                name=tm_input.name,
                role=tm_input.role,
                confidencePercentage=tm_input.confidencePercentage,
                vacations=vacations
            )
            team_members.append(team_member)
        
        # Process holidays
        holidays = []
        if sprint_input.holidays:
            for hol_input in sprint_input.holidays:
                holiday_id = self.generate_id("holiday")
                holiday = Holiday(
                    id=holiday_id,
                    holidayDate=hol_input.holidayDate,
                    name=hol_input.name,
                    description=hol_input.description
                )
                holidays.append(holiday)
        
        # Update the sprint
        updated_sprint = Sprint(
            id=sprint_id,
            sprintName=sprint_input.sprintName,
            sprintDuration=sprint_input.sprintDuration,
            startDate=sprint_input.startDate,
            endDate=sprint_input.endDate,
            teamMembers=team_members,
            holidays=holidays,
            createdAt=old_sprint.createdAt,
            updatedAt=datetime.utcnow()
        )
        
        self.sprints[sprint_id] = updated_sprint
        return updated_sprint
    
    def delete_sprint(self, sprint_id: str) -> bool:
        """
        Delete a sprint by ID.
        
        Returns:
            True if deleted, False if not found
        """
        if sprint_id in self.sprints:
            del self.sprints[sprint_id]
            return True
        return False


# Global database instance
db = Database()
