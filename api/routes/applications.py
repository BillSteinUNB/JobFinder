"""Application tracking endpoints."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from api.schemas import (
    ApplicationResponse,
    ApplicationsResponse,
    ApplicationStatus,
    ApplicationUpdateRequest,
)
from api.routes.jobs import job_to_response

router = APIRouter()

# In-memory application storage (would be a database table in production)
# Maps application_id -> application data
_applications: dict[str, dict] = {}


@router.get("", response_model=ApplicationsResponse)
async def get_applications(request: Request) -> ApplicationsResponse:
    """Get all tracked applications."""
    app_state = request.app.state.app_state
    
    # Get jobs that have been labeled as saved (1)
    saved_jobs = app_state.metadata_db.get_all_jobs(label=1)
    
    applications = []
    for job in saved_jobs:
        # Check if we have application data for this job
        app_data = None
        for app_id, data in _applications.items():
            if data["job_id"] == job.id:
                app_data = (app_id, data)
                break
        
        if app_data:
            app_id, data = app_data
            applications.append(ApplicationResponse(
                id=app_id,
                jobId=job.id,
                job=job_to_response(job),
                status=ApplicationStatus(data["status"]),
                appliedAt=data["applied_at"],
                updatedAt=data["updated_at"],
                notes=data.get("notes", ""),
                nextStep=data.get("next_step"),
                nextStepDate=data.get("next_step_date"),
            ))
        else:
            # Create default application entry for saved job
            app_id = str(uuid4())
            now = datetime.now(timezone.utc).isoformat()
            _applications[app_id] = {
                "job_id": job.id,
                "status": "saved",
                "applied_at": now,
                "updated_at": now,
                "notes": "",
            }
            applications.append(ApplicationResponse(
                id=app_id,
                jobId=job.id,
                job=job_to_response(job),
                status=ApplicationStatus.SAVED,
                appliedAt=now,
                updatedAt=now,
                notes="",
            ))
    
    return ApplicationsResponse(
        applications=applications,
        total=len(applications),
    )


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    request: Request,
    application_id: str,
    body: ApplicationUpdateRequest,
) -> ApplicationResponse:
    """Update application status or notes."""
    app_state = request.app.state.app_state
    
    if application_id not in _applications:
        raise HTTPException(status_code=404, detail="Application not found")
    
    app_data = _applications[application_id]
    now = datetime.now(timezone.utc).isoformat()
    
    # Update fields if provided
    if body.status is not None:
        app_data["status"] = body.status.value
    if body.notes is not None:
        app_data["notes"] = body.notes
    if body.nextStep is not None:
        app_data["next_step"] = body.nextStep
    if body.nextStepDate is not None:
        app_data["next_step_date"] = body.nextStepDate
    
    app_data["updated_at"] = now
    
    # Fetch job
    job = app_state.metadata_db.get_job(app_data["job_id"])
    if job is None:
        raise HTTPException(status_code=404, detail="Associated job not found")
    
    return ApplicationResponse(
        id=application_id,
        jobId=job.id,
        job=job_to_response(job),
        status=ApplicationStatus(app_data["status"]),
        appliedAt=app_data["applied_at"],
        updatedAt=app_data["updated_at"],
        notes=app_data.get("notes", ""),
        nextStep=app_data.get("next_step"),
        nextStepDate=app_data.get("next_step_date"),
    )


@router.post("/{job_id}", response_model=ApplicationResponse)
async def create_application(
    request: Request,
    job_id: str,
) -> ApplicationResponse:
    """Create a new application for a job."""
    app_state = request.app.state.app_state
    
    # Verify job exists
    job = app_state.metadata_db.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if application already exists
    for app_id, data in _applications.items():
        if data["job_id"] == job_id:
            raise HTTPException(status_code=400, detail="Application already exists")
    
    # Create application
    app_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    _applications[app_id] = {
        "job_id": job_id,
        "status": "saved",
        "applied_at": now,
        "updated_at": now,
        "notes": "",
    }
    
    # Also label the job as saved
    app_state.metadata_db.update_label(job_id, 1)
    
    return ApplicationResponse(
        id=app_id,
        jobId=job_id,
        job=job_to_response(job),
        status=ApplicationStatus.SAVED,
        appliedAt=now,
        updatedAt=now,
        notes="",
    )
