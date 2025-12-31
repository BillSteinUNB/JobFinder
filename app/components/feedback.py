"""User feedback component for Streamlit."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Callable

import streamlit as st

from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.db.metadata_db import MetadataDB
    from src.matching.scorer import ScoredJob

logger = get_logger(__name__)


# Feedback labels
LABEL_INTERESTED = 1
LABEL_NOT_INTERESTED = 0


def _init_feedback_state() -> None:
    """Initialize feedback-related session state."""
    if "feedback_history" not in st.session_state:
        st.session_state.feedback_history = {}  # job_id -> label
    if "feedback_count" not in st.session_state:
        st.session_state.feedback_count = {"saved": 0, "rejected": 0}


def get_feedback_for_job(job_id: str) -> int | None:
    """
    Get the current feedback label for a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Label (1=interested, 0=not interested) or None if no feedback
    """
    _init_feedback_state()
    return st.session_state.feedback_history.get(job_id)


def set_feedback_for_job(
    job_id: str,
    label: int,
    metadata_db: "MetadataDB | None" = None,
) -> bool:
    """
    Set feedback label for a job.
    
    Args:
        job_id: Job identifier
        label: Feedback label (1=interested, 0=not interested)
        metadata_db: Optional database to persist feedback
        
    Returns:
        True if feedback was saved successfully
    """
    _init_feedback_state()
    
    # Update session state
    old_label = st.session_state.feedback_history.get(job_id)
    st.session_state.feedback_history[job_id] = label
    
    # Update counts
    if old_label is None:
        if label == LABEL_INTERESTED:
            st.session_state.feedback_count["saved"] += 1
        else:
            st.session_state.feedback_count["rejected"] += 1
    elif old_label != label:
        if label == LABEL_INTERESTED:
            st.session_state.feedback_count["saved"] += 1
            st.session_state.feedback_count["rejected"] -= 1
        else:
            st.session_state.feedback_count["saved"] -= 1
            st.session_state.feedback_count["rejected"] += 1
    
    # Persist to database if available
    if metadata_db is not None:
        try:
            metadata_db.update_label(job_id, label)
        except Exception as e:
            st.error(f"Failed to save feedback: {e}")
            return False
    
    return True


def clear_feedback_for_job(
    job_id: str,
    metadata_db: "MetadataDB | None" = None,
) -> bool:
    """
    Clear feedback for a job.
    
    Args:
        job_id: Job identifier
        metadata_db: Optional database to persist
        
    Returns:
        True if cleared successfully
    """
    _init_feedback_state()
    
    if job_id in st.session_state.feedback_history:
        old_label = st.session_state.feedback_history.pop(job_id)
        
        # Update counts
        if old_label == LABEL_INTERESTED:
            st.session_state.feedback_count["saved"] -= 1
        else:
            st.session_state.feedback_count["rejected"] -= 1
    
    # Clear in database if available
    if metadata_db is not None:
        try:
            metadata_db.update_label(job_id, None)
        except Exception:
            logger.exception("Failed to clear feedback in DB for job_id=%s", job_id)
    
    return True


def render_feedback_buttons(
    job_id: str,
    metadata_db: "MetadataDB | None" = None,
    key_suffix: str = "",
) -> int | None:
    """
    Render Save/Reject feedback buttons for a job.
    
    Args:
        job_id: Job identifier
        metadata_db: Optional database for persistence
        key_suffix: Suffix for unique button keys
        
    Returns:
        Current feedback label or None
    """
    _init_feedback_state()
    
    current_label = get_feedback_for_job(job_id)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        save_variant = "primary" if current_label == LABEL_INTERESTED else "secondary"
        if st.button(
            "Save",
            key=f"save_{job_id}_{key_suffix}",
            type=save_variant,
            help="Mark as interested",
            use_container_width=True,
        ):
            if current_label == LABEL_INTERESTED:
                # Toggle off
                clear_feedback_for_job(job_id, metadata_db)
            else:
                set_feedback_for_job(job_id, LABEL_INTERESTED, metadata_db)
            st.rerun()
    
    with col2:
        reject_variant = "primary" if current_label == LABEL_NOT_INTERESTED else "secondary"
        if st.button(
            "Reject",
            key=f"reject_{job_id}_{key_suffix}",
            type=reject_variant,
            help="Mark as not interested",
            use_container_width=True,
        ):
            if current_label == LABEL_NOT_INTERESTED:
                # Toggle off
                clear_feedback_for_job(job_id, metadata_db)
            else:
                set_feedback_for_job(job_id, LABEL_NOT_INTERESTED, metadata_db)
            st.rerun()
    
    with col3:
        if current_label == LABEL_INTERESTED:
            st.success("Saved", icon="")
        elif current_label == LABEL_NOT_INTERESTED:
            st.error("Rejected", icon="")
    
    return get_feedback_for_job(job_id)


def render_feedback_summary() -> None:
    """Render a summary of feedback given in this session."""
    _init_feedback_state()
    
    saved = st.session_state.feedback_count["saved"]
    rejected = st.session_state.feedback_count["rejected"]
    total = saved + rejected
    
    if total == 0:
        return
    
    st.caption(f"Feedback: {saved} saved, {rejected} rejected")


def render_saved_jobs_section(
    scored_jobs: list["ScoredJob"],
    show_details: bool = True,
) -> list["ScoredJob"]:
    """
    Render a section showing saved jobs.
    
    Args:
        scored_jobs: List of all scored jobs
        show_details: Whether to show job details
        
    Returns:
        List of saved jobs
    """
    _init_feedback_state()
    
    saved_job_ids = {
        job_id for job_id, label in st.session_state.feedback_history.items()
        if label == LABEL_INTERESTED
    }
    
    saved_jobs = [j for j in scored_jobs if j.job.id in saved_job_ids]
    
    if not saved_jobs:
        st.info("No saved jobs yet. Click 'Save' on jobs you're interested in.")
        return []
    
    st.subheader(f"Saved Jobs ({len(saved_jobs)})")
    
    if show_details:
        for job in saved_jobs:
            with st.expander(f"{job.job.title} @ {job.job.company}"):
                st.caption(f"Location: {job.job.location}")
                st.caption(f"Score: {job.total_score:.0%}")
                st.markdown(f"[View Posting]({job.job.url})")
    else:
        for job in saved_jobs:
            st.markdown(f"- **{job.job.title}** @ {job.job.company}")
    
    return saved_jobs


def export_saved_jobs(
    scored_jobs: list["ScoredJob"],
) -> str:
    """
    Export saved jobs as formatted text.
    
    Args:
        scored_jobs: List of all scored jobs
        
    Returns:
        Formatted string with saved jobs
    """
    _init_feedback_state()
    
    saved_job_ids = {
        job_id for job_id, label in st.session_state.feedback_history.items()
        if label == LABEL_INTERESTED
    }
    
    saved_jobs = [j for j in scored_jobs if j.job.id in saved_job_ids]
    
    if not saved_jobs:
        return "No saved jobs."
    
    lines = [
        "# Saved Jobs",
        f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total: {len(saved_jobs)} jobs",
        "",
    ]
    
    for i, sj in enumerate(saved_jobs, 1):
        job = sj.job
        lines.extend([
            f"## {i}. {job.title}",
            f"**Company:** {job.company}",
            f"**Location:** {job.location}",
            f"**Match Score:** {sj.total_score:.0%}",
            f"**URL:** {job.url}",
            "",
        ])
        
        if sj.matched_skills:
            lines.append(f"**Matched Skills:** {', '.join(sj.matched_skills)}")
        
        if sj.missing_skills:
            lines.append(f"**Skills to Learn:** {', '.join(sj.missing_skills)}")
        
        lines.append("")
    
    return "\n".join(lines)


def render_export_button(
    scored_jobs: list["ScoredJob"],
) -> None:
    """
    Render a button to export saved jobs.
    
    Args:
        scored_jobs: List of all scored jobs
    """
    _init_feedback_state()
    
    saved_count = st.session_state.feedback_count["saved"]
    
    if saved_count == 0:
        return
    
    export_text = export_saved_jobs(scored_jobs)
    
    st.download_button(
        label=f"Export Saved Jobs ({saved_count})",
        data=export_text,
        file_name=f"saved_jobs_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown",
        help="Download saved jobs as Markdown",
    )
