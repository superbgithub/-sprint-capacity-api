"""
Sprint Calendar endpoints.
Provides calendar view of sprints with timeline visualization.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import date

from app.config import feature_flags

router = APIRouter(prefix="/v1/calendar", tags=["calendar"])


def check_calendar_feature():
    """Check if sprint calendar feature is enabled."""
    if not feature_flags.is_enabled("sprint_calendar"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint calendar feature is not available"
        )


@router.get("/sprints")
async def get_sprint_calendar(
    start_date: date,
    end_date: date
):
    """
    Get calendar view of sprints within a date range.
    
    Args:
        start_date: Start of calendar period
        end_date: End of calendar period
        
    Returns:
        Calendar view with sprints organized by date
    """
    check_calendar_feature()
    
    # TODO: Implement calendar view logic
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "sprints": [],
        "message": "Sprint calendar feature - coming soon!"
    }
