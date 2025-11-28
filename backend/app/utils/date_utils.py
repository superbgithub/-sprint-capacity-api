"""
Date utility functions for sprint management.
"""
from datetime import date, timedelta


def calculate_working_days(start_date: date, end_date: date, holidays: list = None) -> int:
    """
    Calculate number of working days between start and end dates.
    Excludes weekends (Saturday, Sunday) and holidays.
    
    Args:
        start_date: Start date of the period
        end_date: End date of the period
        holidays: List of holiday dates to exclude
        
    Returns:
        Number of working days (minimum 1, default 10 if dates are invalid)
    """
    if start_date > end_date:
        return 10  # Default
    
    holidays_set = set(holidays) if holidays else set()
    working_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        # Check if it's a weekday (Monday=0, Sunday=6)
        if current_date.weekday() < 5 and current_date not in holidays_set:
            working_days += 1
        current_date += timedelta(days=1)
    
    return max(working_days, 1)  # At least 1 working day
