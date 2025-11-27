"""
Data models for the Team Capacity Management API.
These classes define the structure of data used throughout the application.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date, datetime
from enum import Enum


class RoleEnum(str, Enum):
    """Team member roles"""
    DEVELOPER = "Developer"
    TESTER = "Tester"
    DESIGNER = "Designer"
    PRODUCT_OWNER = "Product Owner"
    SCRUM_MASTER = "Scrum Master"
    TECH_LEAD = "Tech Lead"


class VacationInput(BaseModel):
    """Input model for vacation periods"""
    startDate: date = Field(..., description="Start date of the vacation")
    endDate: date = Field(..., description="End date of the vacation")
    reason: Optional[str] = Field(None, description="Reason for the vacation (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "startDate": "2025-01-10",
                "endDate": "2025-01-12",
                "reason": "Personal leave"
            }
        }


class Vacation(VacationInput):
    """Full vacation model with ID and calculated days"""
    id: str = Field(..., description="Unique identifier for the vacation period")
    daysCount: Optional[int] = Field(None, description="Number of working days in the vacation period")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "vac-001",
                "startDate": "2025-01-10",
                "endDate": "2025-01-12",
                "reason": "Personal leave",
                "daysCount": 3
            }
        }


class TeamMemberInput(BaseModel):
    """Input model for creating/updating team members"""
    name: str = Field(..., description="Full name of the team member")
    role: RoleEnum = Field(..., description="Role of the team member")
    confidencePercentage: Optional[float] = Field(
        100.0,
        ge=0,
        le=100,
        description="Confidence percentage for capacity calculation (0-100)"
    )
    vacations: Optional[List[VacationInput]] = Field(
        default_factory=list,
        description="Vacation periods for this team member during the sprint"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "role": "Developer",
                "confidencePercentage": 85.0,
                "vacations": []
            }
        }


class TeamMember(TeamMemberInput):
    """Full team member model with ID and processed vacations"""
    id: str = Field(..., description="Unique identifier for the team member")
    vacations: Optional[List[Vacation]] = Field(
        default_factory=list,
        description="Vacation periods for this team member during the sprint"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "tm-001",
                "name": "John Doe",
                "role": "Developer",
                "confidencePercentage": 85.0,
                "vacations": []
            }
        }


class HolidayInput(BaseModel):
    """Input model for holidays"""
    holidayDate: date = Field(..., description="Date of the holiday")
    name: str = Field(..., description="Name of the holiday")
    description: Optional[str] = Field(None, description="Additional details about the holiday")

    class Config:
        json_schema_extra = {
            "example": {
                "holidayDate": "2025-01-01",
                "name": "New Year's Day",
                "description": "Public holiday"
            }
        }


class Holiday(HolidayInput):
    """Full holiday model with ID"""
    id: str = Field(..., description="Unique identifier for the holiday")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "holiday-001",
                "holidayDate": "2025-01-01",
                "name": "New Year's Day",
                "description": "Public holiday"
            }
        }


class SprintInput(BaseModel):
    """Input model for creating/updating sprints"""
    sprintName: str = Field(..., description="Name of the sprint")
    sprintDuration: int = Field(..., ge=1, description="Duration of the sprint in days")
    startDate: date = Field(..., description="Start date of the sprint")
    endDate: date = Field(..., description="End date of the sprint")
    teamMembers: List[TeamMemberInput] = Field(default_factory=list, description="List of team members")
    holidays: Optional[List[HolidayInput]] = Field(
        default_factory=list,
        description="Public holidays during the sprint"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sprintName": "Sprint 2025-01",
                "sprintDuration": 14,
                "startDate": "2025-01-06",
                "endDate": "2025-01-19",
                "teamMembers": [
                    {
                        "name": "John Doe",
                        "role": "Developer",
                        "email": "john.doe@example.com",
                        "confidencePercentage": 85.0
                    }
                ],
                "holidays": []
            }
        }


class Sprint(SprintInput):
    """Full sprint model with ID and timestamps"""
    id: str = Field(..., description="Unique identifier for the sprint")
    teamMembers: List[TeamMember] = Field(..., description="List of team members")
    holidays: Optional[List[Holiday]] = Field(
        default_factory=list,
        description="Public holidays during the sprint"
    )
    createdAt: Optional[datetime] = Field(None, description="Timestamp when the sprint was created")
    updatedAt: Optional[datetime] = Field(None, description="Timestamp when the sprint was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "sprint-2025-01",
                "sprintName": "Sprint 2025-01",
                "sprintDuration": 14,
                "startDate": "2025-01-06",
                "endDate": "2025-01-19",
                "teamMembers": [],
                "holidays": [],
                "createdAt": "2025-01-01T10:00:00Z",
                "updatedAt": "2025-01-02T15:30:00Z"
            }
        }


class MemberCapacity(BaseModel):
    """Individual team member capacity breakdown"""
    memberId: str
    memberName: str
    availableDays: float
    vacationDays: float
    confidencePercentage: float
    adjustedCapacity: float = Field(..., description="Capacity adjusted by confidence percentage")


class CapacitySummary(BaseModel):
    """Summary of sprint capacity calculations"""
    sprintId: str = Field(..., description="Sprint identifier")
    totalWorkingDays: int = Field(..., description="Total working days in the sprint")
    totalCapacityDays: float = Field(..., description="Total team capacity in person-days")
    adjustedTotalCapacity: float = Field(..., description="Total capacity adjusted by confidence percentages")
    teamSize: int = Field(..., description="Number of team members")
    holidaysCount: int = Field(..., description="Number of holidays in the sprint")
    vacationDaysCount: float = Field(..., description="Total vacation days across all team members")
    capacityFormula: str = Field(..., description="The formula used for capacity calculation")
    memberCapacity: List[MemberCapacity] = Field(..., description="Individual capacity breakdown per team member")

    class Config:
        json_schema_extra = {
            "example": {
                "sprintId": "sprint-2025-01",
                "totalWorkingDays": 10,
                "totalCapacityDays": 45.5,
                "adjustedTotalCapacity": 38.7,
                "teamSize": 5,
                "holidaysCount": 1,
                "vacationDaysCount": 4.5,
                "capacityFormula": "availableDays * (confidencePercentage / 100)",
                "memberCapacity": []
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[str] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "INVALID_REQUEST",
                "message": "Invalid request parameters",
                "details": "Start date must be before end date"
            }
        }
