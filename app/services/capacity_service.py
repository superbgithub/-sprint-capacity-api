"""
Service for calculating team capacity based on sprint data.
This is where the capacity formula is implemented.
"""
from datetime import date, timedelta
from typing import List
from app.models.schemas import Sprint, MemberCapacity, CapacitySummary


def count_working_days(start_date: date, end_date: date, holidays: List[date]) -> int:
    """
    Count working days between start and end date, excluding weekends and holidays.
    
    Args:
        start_date: Sprint start date
        end_date: Sprint end date
        holidays: List of holiday dates
    
    Returns:
        Number of working days
    """
    working_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        # Check if it's a weekday (Monday=0, Sunday=6)
        if current_date.weekday() < 5:  # Monday to Friday
            # Check if it's not a holiday
            if current_date not in holidays:
                working_days += 1
        current_date += timedelta(days=1)
    
    return working_days


def count_vacation_days(start_date: date, end_date: date, sprint_start: date, sprint_end: date, holidays: List[date]) -> int:
    """
    Count vacation working days that fall within the sprint period.
    
    Args:
        start_date: Vacation start date
        end_date: Vacation end date
        sprint_start: Sprint start date
        sprint_end: Sprint end date
        holidays: List of holiday dates
    
    Returns:
        Number of vacation working days within the sprint
    """
    # Get the overlapping period between vacation and sprint
    overlap_start = max(start_date, sprint_start)
    overlap_end = min(end_date, sprint_end)
    
    # If no overlap, return 0
    if overlap_start > overlap_end:
        return 0
    
    return count_working_days(overlap_start, overlap_end, holidays)


def calculate_capacity(sprint: Sprint) -> CapacitySummary:
    """
    Calculate team capacity for a sprint.
    
    This function:
    1. Calculates total working days (excluding weekends and holidays)
    2. For each team member, calculates their available days (working days - vacation days)
    3. Applies the confidence percentage to get adjusted capacity
    4. Sums up the total capacity for the team
    
    Args:
        sprint: Sprint object with all team and schedule information
    
    Returns:
        CapacitySummary with detailed capacity breakdown
    """
    # Extract holiday dates
    holiday_dates = [holiday.holidayDate for holiday in sprint.holidays] if sprint.holidays else []
    
    # Calculate total working days in the sprint
    total_working_days = count_working_days(sprint.startDate, sprint.endDate, holiday_dates)
    
    # Initialize counters
    total_capacity = 0.0
    adjusted_total_capacity = 0.0
    total_vacation_days = 0.0
    member_capacities = []
    
    # Calculate capacity for each team member
    for member in sprint.teamMembers:
        # Start with full working days
        available_days = float(total_working_days)
        vacation_days = 0.0
        
        # Subtract vacation days
        if member.vacations:
            for vacation in member.vacations:
                vac_days = count_vacation_days(
                    vacation.startDate,
                    vacation.endDate,
                    sprint.startDate,
                    sprint.endDate,
                    holiday_dates
                )
                vacation_days += vac_days
        
        available_days -= vacation_days
        total_vacation_days += vacation_days
        
        # Apply confidence percentage to get adjusted capacity
        confidence = member.confidencePercentage if member.confidencePercentage is not None else 100.0
        adjusted_capacity = available_days * (confidence / 100.0)
        
        # Add to totals
        total_capacity += available_days
        adjusted_total_capacity += adjusted_capacity
        
        # Store individual member capacity
        member_capacities.append(MemberCapacity(
            memberId=member.id,
            memberName=member.name,
            availableDays=available_days,
            vacationDays=vacation_days,
            confidencePercentage=confidence,
            adjustedCapacity=round(adjusted_capacity, 2)
        ))
    
    # The capacity formula used
    formula = "availableDays * (confidencePercentage / 100)"
    
    return CapacitySummary(
        sprintId=sprint.id,
        totalWorkingDays=total_working_days,
        totalCapacityDays=round(total_capacity, 2),
        adjustedTotalCapacity=round(adjusted_total_capacity, 2),
        teamSize=len(sprint.teamMembers),
        holidaysCount=len(sprint.holidays) if sprint.holidays else 0,
        vacationDaysCount=round(total_vacation_days, 2),
        capacityFormula=formula,
        memberCapacity=member_capacities
    )
