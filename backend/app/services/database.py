"""
Database service layer using PostgreSQL with SQLAlchemy.
Provides CRUD operations for sprints and related entities with shared team member model.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.models.schemas import Sprint, SprintInput, TeamMember, Vacation, Holiday, TeamMemberBaseWithId
from app.models.db_models import (
    SprintModel, TeamMemberBaseModel, SprintAssignmentModel, 
    VacationModel, HolidayModel
)
from app.config.database import get_db_context
from app.observability.logging import get_logger
from app.utils.date_utils import calculate_working_days

logger = get_logger(__name__)


class Database:
    '''PostgreSQL database operations for Sprint Capacity API'''
    
    async def get_or_create_team_member(self, session, name: str, role: str) -> TeamMemberBaseModel:
        '''Get existing team member by name or create new one.'''
        result = await session.execute(
            select(TeamMemberBaseModel).where(TeamMemberBaseModel.name == name)
        )
        team_member = result.scalar_one_or_none()
        
        if not team_member:
            team_member = TeamMemberBaseModel(name=name, role=role)
            session.add(team_member)
            await session.flush()
            logger.info(f'Created new team member: {name} ({role})')
        elif team_member.role != role:
            # Update role if changed
            team_member.role = role
            team_member.updated_at = datetime.utcnow()
            logger.info(f'Updated team member role: {name} -> {role}')
        
        return team_member
    
    async def create_sprint(self, sprint_input: SprintInput) -> Sprint:
        '''Create a new sprint with team member assignments, holidays, and vacations.'''
        async with get_db_context() as session:
            # Generate sprint name from sprint number
            sprint_name = f"Sprint {sprint_input.sprintNumber}"
            
            # Calculate working days from start and end dates
            holiday_dates = [h.holidayDate for h in sprint_input.holidays] if sprint_input.holidays else []
            sprint_duration = calculate_working_days(sprint_input.startDate, sprint_input.endDate, holiday_dates)
            
            sprint_model = SprintModel(
                sprint_number=sprint_input.sprintNumber,
                sprint_name=sprint_name,
                start_date=sprint_input.startDate,
                end_date=sprint_input.endDate,
                sprint_duration=sprint_duration,
                confidence_percentage=sprint_input.confidencePercentage if sprint_input.confidencePercentage is not None else 100.0
            )
            session.add(sprint_model)
            await session.flush()
            
            # Add team member assignments
            for tm_input in sprint_input.teamMembers:
                # Get or create team member base
                team_member = await self.get_or_create_team_member(
                    session, 
                    tm_input.name, 
                    tm_input.role
                )
                
                # Create sprint assignment
                assignment = SprintAssignmentModel(
                    sprint_id=sprint_model.id,
                    team_member_id=team_member.id
                )
                session.add(assignment)
                await session.flush()
                
                # Add vacations for this assignment
                for vacation_input in tm_input.vacations if tm_input.vacations else []:
                    vacation = VacationModel(
                        assignment_id=assignment.id,
                        start_date=vacation_input.startDate,
                        end_date=vacation_input.endDate,
                        description=vacation_input.reason if hasattr(vacation_input, 'reason') else ""
                    )
                    session.add(vacation)
            
            # Add holidays to sprint
            for holiday_input in sprint_input.holidays if sprint_input.holidays else []:
                holiday = HolidayModel(
                    sprint_id=sprint_model.id,
                    date=holiday_input.holidayDate,
                    name=holiday_input.name,
                    description=holiday_input.description or ""
                )
                session.add(holiday)
            
            await session.flush()
            await session.refresh(sprint_model, ['team_assignments', 'holidays'])
            for assignment in sprint_model.team_assignments:
                await session.refresh(assignment, ['team_member', 'vacations'])
            
            logger.info(f'Created sprint: {sprint_model.id} ({sprint_model.sprint_number})')
            return self._model_to_schema(sprint_model)
    
    async def get_sprint_by_id(self, sprint_id: str) -> Optional[Sprint]:
        '''Get a sprint by ID with all relationships loaded.'''
        async with get_db_context() as session:
            result = await session.execute(
                select(SprintModel)
                .options(
                    selectinload(SprintModel.team_assignments)
                        .selectinload(SprintAssignmentModel.team_member),
                    selectinload(SprintModel.team_assignments)
                        .selectinload(SprintAssignmentModel.vacations),
                    selectinload(SprintModel.holidays)
                )
                .where(SprintModel.id == sprint_id)
            )
            sprint_model = result.scalar_one_or_none()
            return self._model_to_schema(sprint_model) if sprint_model else None
    
    async def get_all_sprints(self) -> List[Sprint]:
        '''Get all sprints with their relationships.'''
        async with get_db_context() as session:
            result = await session.execute(
                select(SprintModel)
                .options(
                    selectinload(SprintModel.team_assignments)
                        .selectinload(SprintAssignmentModel.team_member),
                    selectinload(SprintModel.team_assignments)
                        .selectinload(SprintAssignmentModel.vacations),
                    selectinload(SprintModel.holidays)
                )
                .order_by(SprintModel.start_date.desc())
            )
            sprint_models = result.scalars().all()
            return [self._model_to_schema(sprint) for sprint in sprint_models]
    
    async def update_sprint(self, sprint_id: str, sprint_input: SprintInput) -> Optional[Sprint]:
        '''Update an existing sprint.'''
        async with get_db_context() as session:
            result = await session.execute(
                select(SprintModel).where(SprintModel.id == sprint_id)
            )
            sprint_model = result.scalar_one_or_none()
            
            if not sprint_model:
                return None
            
            # Calculate working days from start and end dates
            holiday_dates = [h.holidayDate for h in sprint_input.holidays] if sprint_input.holidays else []
            sprint_duration = calculate_working_days(sprint_input.startDate, sprint_input.endDate, holiday_dates)
            
            # Update basic sprint fields
            sprint_model.sprint_number = sprint_input.sprintNumber
            sprint_model.sprint_name = f"Sprint {sprint_input.sprintNumber}"
            sprint_model.start_date = sprint_input.startDate
            sprint_model.end_date = sprint_input.endDate
            sprint_model.sprint_duration = sprint_duration
            sprint_model.confidence_percentage = sprint_input.confidencePercentage if sprint_input.confidencePercentage is not None else 100.0
            sprint_model.updated_at = datetime.utcnow()
            
            # Delete existing assignments (cascades to vacations)
            await session.execute(
                delete(SprintAssignmentModel).where(SprintAssignmentModel.sprint_id == sprint_id)
            )
            
            # Delete existing holidays
            await session.execute(
                delete(HolidayModel).where(HolidayModel.sprint_id == sprint_id)
            )
            
            await session.flush()
            
            # Re-create team member assignments
            for tm_input in sprint_input.teamMembers:
                team_member = await self.get_or_create_team_member(
                    session,
                    tm_input.name,
                    tm_input.role
                )
                
                assignment = SprintAssignmentModel(
                    sprint_id=sprint_model.id,
                    team_member_id=team_member.id
                )
                session.add(assignment)
                await session.flush()
                
                for vacation_input in tm_input.vacations if tm_input.vacations else []:
                    vacation = VacationModel(
                        assignment_id=assignment.id,
                        start_date=vacation_input.startDate,
                        end_date=vacation_input.endDate,
                        description=vacation_input.reason if hasattr(vacation_input, 'reason') else ""
                    )
                    session.add(vacation)
            
            # Re-create holidays
            for holiday_input in sprint_input.holidays if sprint_input.holidays else []:
                holiday = HolidayModel(
                    sprint_id=sprint_model.id,
                    date=holiday_input.holidayDate,
                    name=holiday_input.name,
                    description=holiday_input.description or ""
                )
                session.add(holiday)
            
            await session.flush()
            await session.refresh(sprint_model, ['team_assignments', 'holidays'])
            for assignment in sprint_model.team_assignments:
                await session.refresh(assignment, ['team_member', 'vacations'])
            
            logger.info(f'Updated sprint: {sprint_id}')
            return self._model_to_schema(sprint_model)
    
    async def delete_sprint(self, sprint_id: str) -> bool:
        '''Delete a sprint by ID.'''
        async with get_db_context() as session:
            result = await session.execute(
                select(SprintModel).where(SprintModel.id == sprint_id)
            )
            sprint_model = result.scalar_one_or_none()
            
            if not sprint_model:
                return False
            
            await session.delete(sprint_model)
            await session.flush()
            logger.info(f'Deleted sprint: {sprint_id}')
            return True
    
    async def get_all_team_members(self) -> List[TeamMemberBaseWithId]:
        '''Get all team members in the system.'''
        async with get_db_context() as session:
            result = await session.execute(
                select(TeamMemberBaseModel).order_by(TeamMemberBaseModel.name)
            )
            members = result.scalars().all()
            return [
                TeamMemberBaseWithId(
                    id=member.id,
                    name=member.name,
                    role=member.role
                )
                for member in members
            ]
    
    def _model_to_schema(self, sprint_model: SprintModel) -> Sprint:
        '''Convert database model to Pydantic schema.'''
        # Convert team assignments to team members with vacations
        team_members = []
        for assignment in sprint_model.team_assignments:
            vacations = [
                Vacation(
                    id=vac.id,
                    startDate=vac.start_date,
                    endDate=vac.end_date,
                    reason=vac.description,
                    daysCount=None
                )
                for vac in assignment.vacations
            ]
            
            team_member = TeamMember(
                id=assignment.team_member.id,
                name=assignment.team_member.name,
                role=assignment.team_member.role,
                vacations=vacations
            )
            team_members.append(team_member)
        
        # Convert holidays
        holidays = [
            Holiday(
                id=holiday.id,
                holidayDate=holiday.date,
                name=holiday.name,
                description=holiday.description
            )
            for holiday in sprint_model.holidays
        ]
        
        return Sprint(
            id=sprint_model.id,
            sprintNumber=sprint_model.sprint_number,
            sprintName=sprint_model.sprint_name,
            sprintDuration=sprint_model.sprint_duration,
            startDate=sprint_model.start_date,
            endDate=sprint_model.end_date,
            confidencePercentage=sprint_model.confidence_percentage,
            teamMembers=team_members,
            holidays=holidays,
            createdAt=sprint_model.created_at,
            updatedAt=sprint_model.updated_at
        )


# Singleton instance
_db_instance = None

def get_database() -> Database:
    '''Get the singleton database instance.'''
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
