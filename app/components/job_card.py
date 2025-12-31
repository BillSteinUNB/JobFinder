"""Job card display component for Streamlit."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import streamlit as st

from app.components.feedback import render_feedback_buttons, get_feedback_for_job

if TYPE_CHECKING:
    from src.db.metadata_db import MetadataDB
    from src.matching.scorer import ScoredJob
    from src.matching.evidence import EvidenceResult


def _format_salary(salary_min: float | None, salary_max: float | None) -> str:
    """Format salary range for display."""
    if salary_min is None and salary_max is None:
        return "Not specified"
    
    def fmt(val: float) -> str:
        if val >= 1000:
            return f"${val / 1000:.0f}k"
        return f"${val:.0f}"
    
    if salary_min is not None and salary_max is not None:
        return f"{fmt(salary_min)} - {fmt(salary_max)}"
    elif salary_max is not None:
        return f"Up to {fmt(salary_max)}"
    elif salary_min is not None:
        return f"From {fmt(salary_min)}"
    return "Not specified"


def _format_posted_date(posted_at: datetime) -> str:
    """Format posted date as relative time."""
    now = datetime.now(timezone.utc)
    
    # Handle timezone-naive datetimes
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)
    
    delta = now - posted_at
    days = delta.days
    
    if days == 0:
        return "Today"
    elif days == 1:
        return "Yesterday"
    elif days < 7:
        return f"{days} days ago"
    elif days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif days < 365:
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        return posted_at.strftime("%b %d, %Y")


def _get_score_color(score: float) -> str:
    """Get color for score display based on value."""
    if score >= 0.75:
        return "#28a745"  # Green
    elif score >= 0.6:
        return "#5cb85c"  # Light green
    elif score >= 0.45:
        return "#f0ad4e"  # Orange
    else:
        return "#d9534f"  # Red


def _render_evidence_section(evidence: "EvidenceResult") -> None:
    """Render evidence highlights section."""
    if not evidence or not evidence.matches:
        return
    
    with st.expander("Why This Match?", expanded=False):
        # Top semantic matches
        semantic_matches = [m for m in evidence.matches if m.match_type == "semantic"]
        if semantic_matches:
            st.markdown("**Key Matching Points:**")
            for i, match in enumerate(semantic_matches[:3], 1):
                st.markdown(
                    f"{i}. *Your resume:* \"{match.resume_sentence[:100]}...\"\n\n"
                    f"   *Job needs:* \"{match.job_sentence[:100]}...\"\n\n"
                    f"   Similarity: {match.similarity:.0%}"
                )
                st.divider()
        
        # Skill matches
        if evidence.skill_matches:
            st.markdown("**Matched Skills:**")
            skill_html = " ".join(
                f'<span style="background-color: #d4edda; color: #155724; '
                f'padding: 2px 8px; border-radius: 12px; margin: 2px; '
                f'display: inline-block; font-size: 0.85em;">{skill}</span>'
                for skill in evidence.skill_matches[:10]
            )
            st.markdown(skill_html, unsafe_allow_html=True)
        
        # Keyword matches
        if evidence.keyword_matches:
            st.markdown("**Keyword Overlap:**")
            st.caption(", ".join(evidence.keyword_matches[:15]))


def render_job_card(
    scored_job: "ScoredJob",
    *,
    show_explanation: bool = True,
    show_missing_skills: bool = False,
    show_feedback: bool = True,
    evidence: "EvidenceResult | None" = None,
    metadata_db: "MetadataDB | None" = None,
    index: int = 0,
) -> None:
    """
    Render a single job card with score and details.
    
    Args:
        scored_job: ScoredJob with match data
        show_explanation: Whether to show match explanation
        show_missing_skills: Whether to show missing skills
        show_feedback: Whether to show feedback buttons
        evidence: Optional evidence data for this job
        metadata_db: Optional database for persisting feedback
        index: Index for unique key generation
    """
    job = scored_job.job
    score = scored_job.total_score
    score_color = _get_score_color(score)
    
    # Check if user has given feedback
    feedback = get_feedback_for_job(job.id)
    
    # Create expander with job title and company
    # Add indicator if saved/rejected
    status_icon = ""
    if feedback == 1:
        status_icon = " "
    elif feedback == 0:
        status_icon = " "
    
    header = f"{status_icon}**{job.title}** @ {job.company}"
    
    with st.expander(header, expanded=False):
        # Top row: Location, Posted date, Score
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.caption(f"Location: {job.location}")
        
        with col2:
            st.caption(f"Posted: {_format_posted_date(job.posted_at)}")
        
        with col3:
            # Score badge
            st.markdown(
                f'<span style="background-color: {score_color}; color: white; '
                f'padding: 4px 12px; border-radius: 12px; font-weight: bold;">'
                f'{score:.0%}</span>',
                unsafe_allow_html=True,
            )
        
        # Salary if available
        salary_str = _format_salary(job.salary_min, job.salary_max)
        if salary_str != "Not specified":
            st.caption(f"Salary: {salary_str}")
        
        # Feedback buttons
        if show_feedback:
            render_feedback_buttons(job.id, metadata_db, key_suffix=str(index))
        
        st.divider()
        
        # Explanation
        if show_explanation and scored_job.explanation:
            st.info(scored_job.explanation)
        
        # Evidence section (if available)
        if evidence:
            _render_evidence_section(evidence)
        
        # Matched skills
        if scored_job.matched_skills:
            st.markdown("**Matched Skills:**")
            skill_html = " ".join(
                f'<span style="background-color: #d4edda; color: #155724; '
                f'padding: 2px 8px; border-radius: 12px; margin: 2px; '
                f'display: inline-block; font-size: 0.85em;">{skill}</span>'
                for skill in scored_job.matched_skills
            )
            st.markdown(skill_html, unsafe_allow_html=True)
        
        # Missing skills (if enabled)
        if show_missing_skills and scored_job.missing_skills:
            st.markdown("**Missing Skills:**")
            skill_html = " ".join(
                f'<span style="background-color: #f8d7da; color: #721c24; '
                f'padding: 2px 8px; border-radius: 12px; margin: 2px; '
                f'display: inline-block; font-size: 0.85em;">{skill}</span>'
                for skill in scored_job.missing_skills
            )
            st.markdown(skill_html, unsafe_allow_html=True)
        
        # Description excerpt
        st.markdown("**Description:**")
        description = job.description
        max_chars = 500
        if len(description) > max_chars:
            description = description[:max_chars].rsplit(" ", 1)[0] + "..."
        st.text(description)
        
        # Score breakdown table
        with st.expander("Score Breakdown", expanded=False):
            breakdown = scored_job.breakdown
            weights = scored_job.weights
            contributions = scored_job.contributions
            
            # Create table data
            rows = []
            for component, score_val in breakdown.items():
                weight = weights.get(component, 0)
                contrib = contributions.get(component, 0)
                rows.append({
                    "Component": component.replace("_", " ").title(),
                    "Score": f"{score_val:.2f}",
                    "Weight": f"{weight:.2f}",
                    "Contribution": f"{contrib:.3f}",
                })
            
            # Display as markdown table
            st.markdown("| Component | Score | Weight | Contribution |")
            st.markdown("|-----------|-------|--------|--------------|")
            for row in rows:
                st.markdown(
                    f"| {row['Component']} | {row['Score']} | "
                    f"{row['Weight']} | {row['Contribution']} |"
                )
        
        # Link to original posting
        st.markdown(f"[View Original Posting]({job.url})")


def render_job_list(
    scored_jobs: list["ScoredJob"],
    *,
    show_explanations: bool = True,
    show_missing_skills: bool = False,
    show_feedback: bool = True,
    evidence_map: dict[str, "EvidenceResult"] | None = None,
    metadata_db: "MetadataDB | None" = None,
    min_score: float = 0.0,
) -> None:
    """
    Render a list of job cards.
    
    Args:
        scored_jobs: List of ScoredJob objects (already sorted)
        show_explanations: Whether to show match explanations
        show_missing_skills: Whether to show missing skills
        show_feedback: Whether to show feedback buttons
        evidence_map: Optional dictionary of job_id -> EvidenceResult
        metadata_db: Optional database for persisting feedback
        min_score: Minimum score threshold for display
    """
    # Filter by minimum score
    filtered_jobs = [j for j in scored_jobs if j.total_score >= min_score]
    
    if not filtered_jobs:
        st.warning("No jobs match your criteria. Try adjusting your filters.")
        return
    
    # Summary
    st.markdown(
        f"**Showing {len(filtered_jobs)} jobs** "
        f"(filtered from {len(scored_jobs)} total)"
    )
    
    # Score distribution summary
    if filtered_jobs:
        top_score = filtered_jobs[0].total_score
        avg_score = sum(j.total_score for j in filtered_jobs) / len(filtered_jobs)
        st.caption(f"Top score: {top_score:.0%} | Average: {avg_score:.0%}")
    
    st.divider()
    
    # Render each job card
    for i, scored_job in enumerate(filtered_jobs):
        evidence = None
        if evidence_map:
            evidence = evidence_map.get(scored_job.job.id)
        
        render_job_card(
            scored_job,
            show_explanation=show_explanations,
            show_missing_skills=show_missing_skills,
            show_feedback=show_feedback,
            evidence=evidence,
            metadata_db=metadata_db,
            index=i,
        )


def render_job_summary_row(
    scored_job: "ScoredJob",
    index: int = 0,
) -> bool:
    """
    Render a compact job summary row (for quick browsing).
    
    Args:
        scored_job: ScoredJob with match data
        index: Index for unique key generation
        
    Returns:
        True if user clicked to expand
    """
    job = scored_job.job
    score = scored_job.total_score
    score_color = _get_score_color(score)
    
    # Check feedback status
    feedback = get_feedback_for_job(job.id)
    status_icon = ""
    if feedback == 1:
        status_icon = " "
    elif feedback == 0:
        status_icon = " "
    
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
    
    with col1:
        st.markdown(f"{status_icon}**{job.title}**")
        st.caption(job.company)
    
    with col2:
        st.caption(job.location)
    
    with col3:
        st.caption(_format_posted_date(job.posted_at))
    
    with col4:
        st.markdown(
            f'<span style="background-color: {score_color}; color: white; '
            f'padding: 2px 8px; border-radius: 8px; font-size: 0.9em;">'
            f'{score:.0%}</span>',
            unsafe_allow_html=True,
        )
    
    return False  # Placeholder for click handling
