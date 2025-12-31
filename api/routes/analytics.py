"""Analytics endpoints."""

from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

from api.schemas import (
    AnalyticsResponse,
    FunnelStage,
    SkillMatchScore,
    TimeSeriesPoint,
)
from api.routes.applications import _applications

router = APIRouter()

# Funnel stage colors
FUNNEL_COLORS = {
    "saved": "#3b82f6",      # blue
    "applied": "#8b5cf6",    # purple
    "screening": "#f59e0b",  # amber
    "interview": "#10b981",  # emerald
    "offer": "#22c55e",      # green
    "rejected": "#ef4444",   # red
}


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(request: Request) -> AnalyticsResponse:
    """Get analytics data for the dashboard."""
    app_state = request.app.state.app_state
    
    # Get counts
    total_jobs = app_state.metadata_db.get_job_count()
    
    # Count applications by status
    status_counts: Counter[str] = Counter()
    for app_data in _applications.values():
        status_counts[app_data["status"]] += 1
    
    total_applications = sum(status_counts.values())
    
    # Build funnel data
    funnel_stages = ["saved", "applied", "screening", "interview", "offer", "rejected"]
    funnel = [
        FunnelStage(
            stage=stage.capitalize(),
            count=status_counts.get(stage, 0),
            fill=FUNNEL_COLORS.get(stage, "#6b7280"),
        )
        for stage in funnel_stages
    ]
    
    # Applications over time (last 30 days)
    now = datetime.now(timezone.utc)
    applications_over_time = []
    for days_ago in range(29, -1, -1):
        date = now - timedelta(days=days_ago)
        date_str = date.strftime("%Y-%m-%d")
        
        # Count applications created on this date
        count = 0
        for app_data in _applications.values():
            app_date = app_data.get("applied_at", "")[:10]
            if app_date == date_str:
                count += 1
        
        applications_over_time.append(TimeSeriesPoint(date=date_str, count=count))
    
    # Skill match scores (if resume is uploaded)
    skills_match: list[SkillMatchScore] = []
    avg_match_score = 0.0
    
    profile = app_state.resume_profile
    if profile and profile.skills:
        # Get saved jobs and calculate skill coverage
        saved_jobs = app_state.metadata_db.get_all_jobs(label=1, limit=50)
        
        skill_hit_counts: Counter[str] = Counter()
        skill_total_counts: Counter[str] = Counter()
        match_scores: list[float] = []
        
        for job in saved_jobs:
            from src.processing.text_cleaner import extract_skills_simple
            job_skills = set(extract_skills_simple(job.description))
            
            matched = profile.skills & job_skills
            if job_skills:
                match_scores.append(len(matched) / len(job_skills))
            
            for skill in profile.skills:
                skill_total_counts[skill] += 1
                if skill in job_skills:
                    skill_hit_counts[skill] += 1
        
        # Calculate match percentages for each skill
        for skill in sorted(profile.skills)[:10]:  # Top 10 skills
            total = skill_total_counts.get(skill, 0)
            hits = skill_hit_counts.get(skill, 0)
            score = (hits / total * 100) if total > 0 else 0
            skills_match.append(SkillMatchScore(name=skill, score=round(score, 1)))
        
        if match_scores:
            avg_match_score = sum(match_scores) / len(match_scores) * 100
    
    return AnalyticsResponse(
        applicationsOverTime=applications_over_time,
        funnel=funnel,
        skillsMatch=skills_match,
        totalJobs=total_jobs,
        totalApplications=total_applications,
        avgMatchScore=round(avg_match_score, 1),
    )
