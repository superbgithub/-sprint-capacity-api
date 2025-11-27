"""
API routes for sprint management.
These endpoints handle CRUD operations for sprints.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from datetime import date

from app.models.schemas import Sprint, SprintInput, ErrorResponse, CapacitySummary
from app.services.database import db
from app.services.capacity_service import calculate_capacity

router = APIRouter(prefix="/sprints", tags=["Sprints"])


@router.get(
    "",
    response_model=List[Sprint],
    summary="Get all sprints",
    description="Retrieve a list of all sprints with team capacity information"
)
async def get_sprints(
    startDate: Optional[date] = Query(None, description="Filter sprints starting after this date"),
    endDate: Optional[date] = Query(None, description="Filter sprints ending before this date")
):
    """
    Get all sprints, optionally filtered by date range.
    
    Query Parameters:
    - startDate: Only return sprints that start on or after this date
    - endDate: Only return sprints that end on or before this date
    """
    sprints = db.get_all_sprints()
    
    # Apply filters if provided
    if startDate:
        sprints = [s for s in sprints if s.startDate >= startDate]
    
    if endDate:
        sprints = [s for s in sprints if s.endDate <= endDate]
    
    return sprints


@router.post(
    "",
    response_model=Sprint,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sprint",
    description="Create a new sprint with team capacity information"
)
async def create_sprint(sprint_input: SprintInput):
    """
    Create a new sprint.
    
    The system will automatically:
    - Generate unique IDs for the sprint, team members, holidays, and vacations
    - Set creation and update timestamps
    
    Returns the created sprint with all generated IDs.
    """
    # Validate that start date is before end date
    if sprint_input.startDate >= sprint_input.endDate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_REQUEST",
                "message": "Invalid request parameters",
                "details": "Start date must be before end date"
            }
        )
    
    sprint = db.create_sprint(sprint_input)
    return sprint


@router.get(
    "/{sprintId}",
    response_model=Sprint,
    summary="Get sprint by ID",
    description="Retrieve detailed information about a specific sprint"
)
async def get_sprint_by_id(sprintId: str):
    """
    Get a specific sprint by its ID.
    
    Returns 404 if the sprint is not found.
    """
    sprint = db.get_sprint(sprintId)
    
    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Sprint not found",
                "details": f"No sprint found with ID: {sprintId}"
            }
        )
    
    return sprint


@router.put(
    "/{sprintId}",
    response_model=Sprint,
    summary="Update sprint",
    description="Update an existing sprint's information"
)
async def update_sprint(sprintId: str, sprint_input: SprintInput):
    """
    Update an existing sprint.
    
    All team members, holidays, and vacations will be replaced with the new data.
    New IDs will be generated for team members, holidays, and vacations.
    """
    # Validate that start date is before end date
    if sprint_input.startDate >= sprint_input.endDate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_REQUEST",
                "message": "Invalid request parameters",
                "details": "Start date must be before end date"
            }
        )
    
    sprint = db.update_sprint(sprintId, sprint_input)
    
    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Sprint not found",
                "details": f"No sprint found with ID: {sprintId}"
            }
        )
    
    return sprint


@router.delete(
    "/{sprintId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete sprint",
    description="Delete a sprint from the system"
)
async def delete_sprint(sprintId: str):
    """
    Delete a sprint by ID.
    
    Returns 204 No Content on success.
    Returns 404 if the sprint is not found.
    """
    success = db.delete_sprint(sprintId)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Sprint not found",
                "details": f"No sprint found with ID: {sprintId}"
            }
        )
    
    return None


@router.get(
    "/{sprintId}/capacity",
    response_model=CapacitySummary,
    summary="Get sprint capacity summary",
    description="Calculate and retrieve the total capacity for a sprint",
    tags=["Capacity"]
)
async def get_sprint_capacity(sprintId: str):
    """
    Calculate the capacity for a sprint.
    
    This endpoint:
    1. Retrieves the sprint data
    2. Calculates working days (excluding weekends and holidays)
    3. Calculates each team member's available days (subtracting vacations)
    4. Applies confidence percentage to get adjusted capacity
    5. Returns a detailed breakdown
    
    Returns 404 if the sprint is not found.
    """
    sprint = db.get_sprint(sprintId)
    
    if not sprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Sprint not found",
                "details": f"No sprint found with ID: {sprintId}"
            }
        )
    
    capacity_summary = calculate_capacity(sprint)
    return capacity_summary
