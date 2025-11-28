"""
Unit tests for capacity calculation service.
Tests individual functions in isolation.
"""
import pytest
from datetime import date, timedelta
from app.services.capacity_service import (
    count_working_days,
    count_vacation_days,
    calculate_capacity
)
from app.models.schemas import (
    Sprint, TeamMember, Holiday, Vacation, RoleEnum
)


class TestCountWorkingDays:
    """Test working days calculation"""
    
    def test_simple_week_no_holidays(self):
        """Test counting working days in a simple week"""
        start = date(2025, 11, 26)  # Wednesday
        end = date(2025, 11, 28)    # Friday
        holidays = []
        
        result = count_working_days(start, end, holidays)
        assert result == 3  # Wed, Thu, Fri
    
    def test_week_with_weekend(self):
        """Test that weekends are excluded"""
        start = date(2025, 11, 26)  # Wednesday
        end = date(2025, 12, 1)     # Monday
        holidays = []
        
        result = count_working_days(start, end, holidays)
        assert result == 4  # Wed, Thu, Fri, Mon (excludes Sat, Sun)
    
    def test_week_with_holiday(self):
        """Test that holidays are excluded"""
        start = date(2025, 11, 26)  # Wednesday
        end = date(2025, 11, 28)    # Friday
        holidays = [date(2025, 11, 27)]  # Thursday is holiday
        
        result = count_working_days(start, end, holidays)
        assert result == 2  # Wed, Fri only
    
    def test_single_day(self):
        """Test single day calculation"""
        start = date(2025, 11, 26)
        end = date(2025, 11, 26)
        holidays = []
        
        result = count_working_days(start, end, holidays)
        assert result == 1
    
    def test_weekend_only(self):
        """Test weekend-only period"""
        start = date(2025, 11, 29)  # Saturday
        end = date(2025, 11, 30)    # Sunday
        holidays = []
        
        result = count_working_days(start, end, holidays)
        assert result == 0


class TestCountVacationDays:
    """Test vacation days calculation"""
    
    def test_vacation_within_sprint(self):
        """Vacation fully within sprint period"""
        vac_start = date(2025, 11, 27)
        vac_end = date(2025, 11, 29)
        sprint_start = date(2025, 11, 26)
        sprint_end = date(2025, 12, 9)
        holidays = []
        
        result = count_vacation_days(vac_start, vac_end, sprint_start, sprint_end, holidays)
        assert result == 2  # Wed, Thu, Fri (Fri-Sat-Sun, only Fri counts)
    
    def test_vacation_before_sprint(self):
        """Vacation completely before sprint"""
        vac_start = date(2025, 11, 20)
        vac_end = date(2025, 11, 22)
        sprint_start = date(2025, 11, 26)
        sprint_end = date(2025, 12, 9)
        holidays = []
        
        result = count_vacation_days(vac_start, vac_end, sprint_start, sprint_end, holidays)
        assert result == 0
    
    def test_vacation_overlapping_sprint_start(self):
        """Vacation starts before sprint, ends within sprint"""
        vac_start = date(2025, 11, 24)
        vac_end = date(2025, 11, 27)
        sprint_start = date(2025, 11, 26)
        sprint_end = date(2025, 12, 9)
        holidays = []
        
        result = count_vacation_days(vac_start, vac_end, sprint_start, sprint_end, holidays)
        assert result == 2  # Wed, Thu only
    
    def test_vacation_with_holiday(self):
        """Vacation includes a holiday"""
        vac_start = date(2025, 11, 26)
        vac_end = date(2025, 11, 28)
        sprint_start = date(2025, 11, 26)
        sprint_end = date(2025, 12, 9)
        holidays = [date(2025, 11, 27)]
        
        result = count_vacation_days(vac_start, vac_end, sprint_start, sprint_end, holidays)
        assert result == 2  # Wed, Fri (Thu is holiday, doesn't count as vacation)


class TestCalculateCapacity:
    """Test full capacity calculation"""
    
    def test_single_member_no_vacation(self):
        """Test capacity for one team member without vacation"""
        sprint = Sprint(
            id="test-sprint",
            sprintNumber="25-01",
            sprintName="Sprint 25-01",
            sprintDuration=3,
            confidencePercentage=100.0,
            startDate=date(2025, 11, 26),  # Wednesday
            endDate=date(2025, 11, 28),    # Friday
            teamMembers=[
                TeamMember(
                    id="tm-001",
                    name="John Doe",
                    role=RoleEnum.DEVELOPER,
                    vacations=[]
                )
            ],
            holidays=[],
            createdAt=None,
            updatedAt=None
        )
        
        capacity = calculate_capacity(sprint)
        
        assert capacity.totalWorkingDays == 3
        assert capacity.totalCapacityDays == 3.0
        assert capacity.adjustedTotalCapacity == 3.0
        assert capacity.teamSize == 1
        assert len(capacity.memberCapacity) == 1
        assert capacity.memberCapacity[0].adjustedCapacity == 3.0
    
    def test_single_member_with_confidence(self):
        """Test capacity with confidence percentage"""
        sprint = Sprint(
            id="test-sprint",
            sprintNumber="25-02",
            sprintName="Sprint 25-02",
            sprintDuration=3,
            confidencePercentage=80.0,  # 80% confidence at sprint level
            startDate=date(2025, 11, 26),
            endDate=date(2025, 11, 28),
            teamMembers=[
                TeamMember(
                    id="tm-001",
                    name="John Doe",
                    role=RoleEnum.DEVELOPER,
                    vacations=[]
                )
            ],
            holidays=[],
            createdAt=None,
            updatedAt=None
        )
        
        capacity = calculate_capacity(sprint)
        
        assert capacity.totalCapacityDays == 3.0
        assert capacity.adjustedTotalCapacity == 2.4  # 3 * 0.8
        assert capacity.memberCapacity[0].adjustedCapacity == 2.4
    
    def test_multiple_members(self):
        """Test capacity for multiple team members"""
        sprint = Sprint(
            id="test-sprint",
            sprintNumber="25-03",
            sprintName="Sprint 25-03",
            sprintDuration=3,
            confidencePercentage=90.0,  # Sprint-level confidence
            startDate=date(2025, 11, 26),
            endDate=date(2025, 11, 28),
            teamMembers=[
                TeamMember(
                    id="tm-001",
                    name="John Doe",
                    role=RoleEnum.DEVELOPER,
                    vacations=[]
                ),
                TeamMember(
                    id="tm-002",
                    name="Jane Smith",
                    role=RoleEnum.TESTER,
                    vacations=[]
                )
            ],
            holidays=[],
            createdAt=None,
            updatedAt=None
        )
        
        capacity = calculate_capacity(sprint)
        
        assert capacity.teamSize == 2
        assert capacity.totalCapacityDays == 6.0  # 3 days * 2 people
        assert capacity.adjustedTotalCapacity == 5.4  # 6 * 0.9 (sprint-level confidence)
    
    def test_member_with_vacation(self):
        """Test capacity with vacation"""
        sprint = Sprint(
            id="test-sprint",
            sprintNumber="25-04",
            sprintName="Sprint 25-04",
            sprintDuration=3,
            confidencePercentage=100.0,
            startDate=date(2025, 11, 26),
            endDate=date(2025, 11, 28),
            teamMembers=[
                TeamMember(
                    id="tm-001",
                    name="John Doe",
                    role=RoleEnum.DEVELOPER,
                    vacations=[
                        Vacation(
                            id="vac-001",
                            startDate=date(2025, 11, 27),
                            endDate=date(2025, 11, 27),
                            daysCount=None
                        )
                    ]
                )
            ],
            holidays=[],
            createdAt=None,
            updatedAt=None
        )
        
        capacity = calculate_capacity(sprint)
        
        assert capacity.totalWorkingDays == 3
        assert capacity.vacationDaysCount == 1.0
        assert capacity.memberCapacity[0].availableDays == 2.0  # 3 - 1
        assert capacity.memberCapacity[0].adjustedCapacity == 2.0
    
    def test_sprint_with_holiday(self):
        """Test capacity with public holiday"""
        sprint = Sprint(
            id="test-sprint",
            sprintNumber="25-05",
            sprintName="Sprint 25-05",
            sprintDuration=2,
            confidencePercentage=100.0,
            startDate=date(2025, 11, 26),
            endDate=date(2025, 11, 28),
            teamMembers=[
                TeamMember(
                    id="tm-001",
                    name="John Doe",
                    role=RoleEnum.DEVELOPER,
                    vacations=[]
                )
            ],
            holidays=[
                Holiday(
                    id="hol-001",
                    holidayDate=date(2025, 11, 27),
                    name="Thanksgiving"
                )
            ],
            createdAt=None,
            updatedAt=None
        )
        
        capacity = calculate_capacity(sprint)
        
        assert capacity.totalWorkingDays == 2  # Holiday excluded
        assert capacity.holidaysCount == 1
        assert capacity.totalCapacityDays == 2.0
        assert capacity.adjustedTotalCapacity == 2.0
