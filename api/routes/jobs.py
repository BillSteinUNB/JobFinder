"""Job search and management endpoints."""

from fastapi import APIRouter, HTTPException, Query, Request

from api.schemas import (
    CompanyResponse,
    JobLabelRequest,
    JobResponse,
    JobSearchResponse,
    JobType,
    MatchedSkill,
)
from src.data_collection.schema import Job
from src.matching.scorer import ScoredJob

router = APIRouter()


def job_to_response(job: Job, scored: ScoredJob | None = None) -> JobResponse:
    """Convert internal Job model to API response."""
    # Determine job type from contract_time/contract_type
    job_type = JobType.FULL_TIME
    if job.contract_time == "part_time":
        job_type = JobType.PART_TIME
    elif job.contract_type == "contract":
        job_type = JobType.CONTRACT
    
    # Check if remote
    is_remote = "remote" in job.location.lower()
    
    # Build matched skills if we have scoring data
    matched_skills: list[MatchedSkill] = []
    if scored:
        for skill in scored.matched_skills:
            matched_skills.append(MatchedSkill(name=skill, match=True))
        for skill in scored.missing_skills[:5]:  # Limit missing skills shown
            matched_skills.append(MatchedSkill(name=skill, match=False))
    
    return JobResponse(
        id=job.id,
        title=job.title,
        company=CompanyResponse(
            name=job.company,
            logo="",
            location=job.location,
            size="",
            website="",
        ),
        location=job.location,
        type=job_type,
        salaryMin=job.salary_min or 0,
        salaryMax=job.salary_max or 0,
        postedAt=job.posted_at.isoformat(),
        matchScore=scored.total_score * 100 if scored else 0,
        skills=scored.matched_skills if scored else [],
        matchedSkills=matched_skills,
        description=job.description,
        requirements=[],  # Could extract from description
        benefits=[],      # Could extract from description
        isRemote=is_remote,
        status="new",
        url=job.url,
        category=job.category,
        explanation=scored.explanation if scored else None,
        breakdown=scored.breakdown if scored else None,
    )


@router.get("/search", response_model=JobSearchResponse)
async def search_jobs(
    request: Request,
    query: str | None = Query(None, description="Search query"),
    location: str | None = Query(None, description="Location filter"),
    min_salary: float | None = Query(None, description="Minimum salary"),
    remote_only: bool = Query(False, description="Remote jobs only"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> JobSearchResponse:
    """
    Search jobs with semantic matching against resume.
    
    If a resume is uploaded, returns jobs ranked by match score.
    Otherwise returns jobs sorted by recency.
    """
    app_state = request.app.state.app_state
    profile = app_state.resume_profile
    
    # If no resume, return jobs from metadata DB
    if profile is None:
        jobs = app_state.metadata_db.get_all_jobs(limit=limit, offset=offset)
        total = app_state.metadata_db.get_job_count()
        
        return JobSearchResponse(
            jobs=[job_to_response(job) for job in jobs],
            total=total,
            limit=limit,
            offset=offset,
            hasMore=offset + len(jobs) < total,
        )
    
    # Semantic search with resume embedding
    vector_db = app_state.vector_db
    
    # Query vector DB
    results = vector_db.query(
        query_embedding=profile.embedding,
        n_results=min(limit + offset + 50, 200),  # Get extra for filtering
    )
    
    if not results["ids"] or not results["ids"][0]:
        return JobSearchResponse(
            jobs=[],
            total=0,
            limit=limit,
            offset=offset,
            hasMore=False,
        )
    
    # Get job IDs and distances
    job_ids = results["ids"][0]
    distances = results["distances"][0] if results.get("distances") else [0.5] * len(job_ids)
    
    # Fetch full job data from metadata DB
    jobs_map = app_state.metadata_db.get_jobs_by_ids(job_ids)
    
    # Score jobs
    jobs_to_score = []
    distances_to_score = []
    for job_id, distance in zip(job_ids, distances):
        if job_id in jobs_map:
            job = jobs_map[job_id]
            # Apply filters
            if location and location.lower() not in job.location.lower():
                continue
            if min_salary and job.salary_max and job.salary_max < min_salary:
                continue
            if remote_only and "remote" not in job.location.lower():
                continue
            jobs_to_score.append(job)
            distances_to_score.append(distance)
    
    # Score with hybrid scorer
    scored_jobs = app_state.scorer.score_jobs(
        jobs=jobs_to_score,
        distances=distances_to_score,
        resume_profile=profile,
    )
    
    # Paginate
    total = len(scored_jobs)
    paginated = scored_jobs[offset:offset + limit]
    
    return JobSearchResponse(
        jobs=[job_to_response(sj.job, sj) for sj in paginated],
        total=total,
        limit=limit,
        offset=offset,
        hasMore=offset + len(paginated) < total,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(request: Request, job_id: str) -> JobResponse:
    """Get a single job by ID with match details."""
    app_state = request.app.state.app_state
    
    job = app_state.metadata_db.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Score against resume if available
    scored: ScoredJob | None = None
    profile = app_state.resume_profile
    if profile is not None:
        # Get distance from vector DB
        try:
            results = app_state.vector_db.query(
                query_embedding=profile.embedding,
                n_results=1,
                where={"job_id": job_id},
            )
            distance = results["distances"][0][0] if results.get("distances") and results["distances"][0] else 0.5
        except Exception:
            distance = 0.5
        
        scored = app_state.scorer.score_job(job, distance, profile)
    
    return job_to_response(job, scored)


@router.patch("/{job_id}/label")
async def label_job(
    request: Request,
    job_id: str,
    body: JobLabelRequest,
) -> dict[str, str]:
    """
    Label a job as saved (1) or rejected (0).
    
    This is used for the application tracking system.
    """
    app_state = request.app.state.app_state
    
    success = app_state.metadata_db.update_label(job_id, body.label)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    
    action = "saved" if body.label == 1 else "rejected"
    return {"status": "ok", "message": f"Job {action}"}
