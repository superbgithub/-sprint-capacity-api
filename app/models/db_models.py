"""
SQLAlchemy database models for Sprint Capacity API.
"""
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from app.config.database import Base


def generate_uuid():
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


class TeamMemberBaseModel(Base):
    """
    Team Member Base database model.
    Stores shared team member information that persists across all sprints.
    """
    __tablename__ = "team_members_base"
    
    id = Column(String, primary_key=True, default=lambda: f"tm-{uuid.uuid4().hex[:8]}")
    name = Column(String(255), nullable=False, unique=True, index=True)
    role = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sprint_assignments = relationship("SprintAssignmentModel", back_populates="team_member", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TeamMemberBase(id='{self.id}', name='{self.name}', role='{self.role}')>"


class SprintModel(Base):
    """
    Sprint database model.
    Represents a sprint with its basic information and relationships to team members.
    """
    __tablename__ = "sprints"
    
    id = Column(String, primary_key=True, default=lambda: f"sprint-{uuid.uuid4().hex[:8]}")
    sprint_number = Column(String(10), nullable=False, unique=True, index=True)  # Format: YY-NN (e.g., "25-01")
    sprint_name = Column(String(255), nullable=False, index=True)  # Auto-generated: "Sprint 25-01"
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    sprint_duration = Column(Integer, nullable=False)
    confidence_percentage = Column(Float, nullable=False, default=100.0)  # Sprint-level confidence for capacity forecasting (0-100)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team_assignments = relationship("SprintAssignmentModel", back_populates="sprint", cascade="all, delete-orphan")
    holidays = relationship("HolidayModel", back_populates="sprint", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Sprint(id='{self.id}', number='{self.sprint_number}', name='{self.sprint_name}', start='{self.start_date}', end='{self.end_date}')>"


class SprintAssignmentModel(Base):
    """
    Sprint Assignment database model.
    Links team members to sprints with sprint-specific information (confidence, vacations).
    """
    __tablename__ = "sprint_assignments"
    
    id = Column(String, primary_key=True, default=lambda: f"assign-{uuid.uuid4().hex[:8]}")
    sprint_id = Column(String, ForeignKey("sprints.id", ondelete="CASCADE"), nullable=False, index=True)
    team_member_id = Column(String, ForeignKey("team_members_base.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sprint = relationship("SprintModel", back_populates="team_assignments")
    team_member = relationship("TeamMemberBaseModel", back_populates="sprint_assignments")
    vacations = relationship("VacationModel", back_populates="assignment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SprintAssignment(id='{self.id}', sprint_id='{self.sprint_id}', member_id='{self.team_member_id}')>"


class HolidayModel(Base):
    """
    Holiday database model.
    Represents a public holiday during a sprint.
    """
    __tablename__ = "holidays"
    
    id = Column(String, primary_key=True, default=lambda: f"holiday-{uuid.uuid4().hex[:8]}")
    sprint_id = Column(String, ForeignKey("sprints.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    sprint = relationship("SprintModel", back_populates="holidays")
    
    def __repr__(self):
        return f"<Holiday(id='{self.id}', date='{self.date}', name='{self.name}')>"


class VacationModel(Base):
    """
    Vacation database model.
    Represents a vacation period for a team member during a specific sprint.
    """
    __tablename__ = "vacations"
    
    id = Column(String, primary_key=True, default=lambda: f"vacation-{uuid.uuid4().hex[:8]}")
    assignment_id = Column(String, ForeignKey("sprint_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    assignment = relationship("SprintAssignmentModel", back_populates="vacations")
    
    def __repr__(self):
        return f"<Vacation(id='{self.id}', assignment_id='{self.assignment_id}', start='{self.start_date}', end='{self.end_date}')>"
