"""Job Finder - Streamlit Dashboard for Job Recommendations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st

from app.components.resume_upload import render_resume_upload, get_resume_data
from app.components.filters import render_filters, FilterState
from app.components.job_card import render_job_list
from app.components.skill_gap import render_skill_gap_full
from app.components.feedback import (
    render_feedback_summary,
    render_saved_jobs_section,
    render_export_button,
)

from src.db.metadata_db import MetadataDB
from src.db.vector_db import VectorDB
from src.matching.embeddings import EmbeddingManager, compute_version_id
from src.matching.scorer import HybridScorer, ResumeProfile, ScoredJob
from src.matching.evidence import EvidenceExtractor
from src.evaluation.metrics import evaluate_recommendations, render_metrics_summary
from src.data_collection.schema import Job
from src.utils.config import get_settings
from src.utils.logger import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


# =============================================================================
# Cached Resources (expensive objects loaded once)
# =============================================================================


@st.cache_resource
def get_embedding_manager() -> EmbeddingManager:
    """Get or create the embedding manager (cached)."""
    return EmbeddingManager()


@st.cache_resource
def get_metadata_db() -> MetadataDB:
    """Get or create the metadata database handler (cached)."""
    return MetadataDB()


@st.cache_resource
def get_vector_db() -> VectorDB:
    """Get or create the vector database handler (cached)."""
    embedding_manager = get_embedding_manager()
    embed_config = embedding_manager.config()
    return VectorDB(embedding_version=embed_config.version_id)


@st.cache_resource
def get_evidence_extractor() -> EvidenceExtractor:
    """Get or create the evidence extractor (cached)."""
    embedding_manager = get_embedding_manager()
    return EvidenceExtractor(
        embedding_manager=embedding_manager,
        top_k_sentences=5,
        similarity_threshold=0.5,
    )


# =============================================================================
# Session State Initialization
# =============================================================================


def init_session_state() -> None:
    """Initialize all session state keys."""
    defaults = {
        "search_results": [],
        "evidence_map": {},
        "last_search_time": None,
        "error_message": None,
        "active_tab": "results",
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


# =============================================================================
# Search Pipeline
# =============================================================================


def build_resume_profile(
    resume_data: dict,
    filters: FilterState,
    embedding_manager: EmbeddingManager,
) -> ResumeProfile | None:
    """
    Build a ResumeProfile from resume data and filters.
    
    Args:
        resume_data: Data from get_resume_data()
        filters: Current filter settings
        embedding_manager: Embedding manager for computing embeddings
        
    Returns:
        ResumeProfile or None if no resume loaded
    """
    if not resume_data.get("clean_text"):
        return None
    
    # Get or compute embedding
    embedding = resume_data.get("embedding")
    if embedding is None:
        with st.spinner("Computing resume embedding..."):
            embedding = embedding_manager.embed_text(resume_data["clean_text"])
            embedding = embedding.tolist()
    
    return ResumeProfile(
        raw_text=resume_data.get("raw_text", ""),
        clean_text=resume_data["clean_text"],
        skills=set(resume_data.get("skills", [])),
        embedding=embedding,
        preferred_location=filters.location_text if filters.location_text else None,
        min_salary=filters.salary_min,
    )


def run_search(
    resume_profile: ResumeProfile,
    filters: FilterState,
    metadata_db: MetadataDB,
    vector_db: VectorDB,
) -> list[ScoredJob]:
    """
    Run the full search pipeline.
    
    Args:
        resume_profile: Processed resume data
        filters: Filter settings
        metadata_db: Metadata database
        vector_db: Vector database
        
    Returns:
        List of ScoredJob, sorted by score descending
    """
    # Build where clause for recency filter
    where_clause = None
    if filters.recency_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=filters.recency_days)
        where_clause = {"posted_at": {"$gte": cutoff.isoformat()}}
    
    # Query vector database
    results = vector_db.query(
        query_embedding=resume_profile.embedding,
        n_results=filters.top_k * 2,  # Get more to account for filtering
        where=where_clause,
    )
    
    if not results["ids"] or not results["ids"][0]:
        return []
    
    # Extract IDs and distances
    job_ids = results["ids"][0]
    distances = results["distances"][0] if results.get("distances") else [0.5] * len(job_ids)
    
    # Bulk fetch job data from metadata DB (fixes N+1 query issue)
    job_map = metadata_db.get_jobs_by_ids(job_ids)
    
    # Build ordered list preserving Chroma's ranking
    jobs: list[Job] = []
    job_distances: list[float] = []
    
    for job_id, distance in zip(job_ids, distances):
        job = job_map.get(job_id)
        if job is None:
            continue
        # Apply source filter
        if filters.sources and job.source not in filters.sources:
            continue
        jobs.append(job)
        job_distances.append(distance)
    
    if not jobs:
        return []
    
    # Score jobs
    scorer = HybridScorer()
    scored_jobs = scorer.score_jobs(jobs, job_distances, resume_profile)
    
    # Apply minimum score filter and limit
    filtered = [j for j in scored_jobs if j.total_score >= filters.min_score]
    return filtered[:filters.top_k]


def extract_evidence_for_jobs(
    scored_jobs: list[ScoredJob],
    resume_text: str,
    evidence_extractor: EvidenceExtractor,
    max_jobs: int = 20,
) -> dict:
    """
    Extract evidence for top jobs.
    
    Args:
        scored_jobs: List of scored jobs
        resume_text: Clean resume text
        evidence_extractor: Evidence extractor instance
        max_jobs: Maximum number of jobs to extract evidence for
        
    Returns:
        Dictionary mapping job_id to EvidenceResult
    """
    evidence_map = {}
    failures = 0
    
    for job in scored_jobs[:max_jobs]:
        try:
            evidence = evidence_extractor.extract_evidence(
                job.job.id,
                resume_text,
                job.job.description,
            )
            evidence_map[job.job.id] = evidence
        except Exception:
            failures += 1
            logger.exception("Evidence extraction failed for job_id=%s", job.job.id)
    
    if failures:
        logger.warning("Evidence extraction failed for %d job(s)", failures)
    
    return evidence_map


# =============================================================================
# Main App
# =============================================================================


def main() -> None:
    """Main Streamlit app entry point."""
    st.set_page_config(
        page_title="Job Finder",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    init_session_state()
    
    # Title
    st.title("Job Finder")
    st.caption("AI-powered job recommendations based on your resume")
    
    # Check if databases exist
    settings = get_settings()
    db_exists = settings.metadata_db_path.exists()
    
    if not db_exists:
        st.error(
            "Database not found. Please run the setup script first:\n\n"
            "```bash\npython scripts/setup_db.py\npython scripts/collect_jobs.py\n"
            "python scripts/build_vector_index.py\n```"
        )
        return
    
    # Load resources
    try:
        embedding_manager = get_embedding_manager()
        metadata_db = get_metadata_db()
        vector_db = get_vector_db()
        evidence_extractor = get_evidence_extractor()
    except Exception as e:
        st.error(f"Failed to load resources: {e}")
        return
    
    # Check vector index
    index_count = 0
    try:
        index_info = vector_db.info()
        index_count = index_info.count
        if index_count == 0:
            st.warning(
                "Vector index is empty. Please run the indexing script:\n\n"
                "```bash\npython scripts/build_vector_index.py\n```"
            )
    except Exception as e:
        st.warning(f"Could not check vector index: {e}")
    
    # Sidebar
    with st.sidebar:
        # Resume upload
        has_resume = render_resume_upload(embedding_manager)
        
        st.divider()
        
        # Get available sources for filter
        try:
            job_count = metadata_db.get_job_count()
            available_sources = ["adzuna"]  # Hardcoded for now
        except Exception:
            job_count = 0
            available_sources = []
        
        # Filters
        filters = render_filters(available_sources)
        
        st.divider()
        
        # Database stats
        st.caption(f"Jobs in database: {job_count:,}")
        if index_count > 0:
            st.caption(f"Jobs in vector index: {index_count:,}")
        
        # Feedback summary
        render_feedback_summary()
        
        st.divider()
        
        # Search button
        search_disabled = not has_resume
        search_help = "Upload your resume first" if not has_resume else "Find matching jobs"
        
        if st.button(
            "Find Matching Jobs",
            type="primary",
            disabled=search_disabled,
            help=search_help,
            use_container_width=True,
        ):
            # Get resume data
            resume_data = get_resume_data()
            
            # Build profile
            resume_profile = build_resume_profile(
                resume_data, filters, embedding_manager
            )
            
            if resume_profile is None:
                st.error("Could not process resume. Please try again.")
            else:
                # Run search
                with st.spinner("Searching for matching jobs..."):
                    try:
                        results = run_search(
                            resume_profile, filters, metadata_db, vector_db
                        )
                        st.session_state.search_results = results
                        st.session_state.last_search_time = datetime.now(timezone.utc)
                        st.session_state.error_message = None
                        
                        # Extract evidence for top results
                        if results:
                            with st.spinner("Analyzing matches..."):
                                evidence_map = extract_evidence_for_jobs(
                                    results,
                                    resume_data["clean_text"],
                                    evidence_extractor,
                                )
                                st.session_state.evidence_map = evidence_map
                        
                    except Exception as e:
                        st.session_state.error_message = str(e)
                        st.session_state.search_results = []
        
        # Export button for saved jobs
        results = st.session_state.search_results
        if results:
            render_export_button(results)
    
    # Main content area
    if st.session_state.error_message:
        st.error(f"Search failed: {st.session_state.error_message}")
    
    results = st.session_state.search_results
    resume_data = get_resume_data() if has_resume else {}
    
    if results:
        # Show search metadata
        if st.session_state.last_search_time:
            st.caption(
                f"Search completed at "
                f"{st.session_state.last_search_time.strftime('%H:%M:%S')}"
            )
        
        # Tabs for different views
        tab_results, tab_skills, tab_saved, tab_metrics = st.tabs([
            "Job Results",
            "Skill Gap Analysis",
            "Saved Jobs",
            "Metrics",
        ])
        
        with tab_results:
            # Render job list with feedback and evidence
            render_job_list(
                results,
                show_explanations=filters.show_explanations,
                show_missing_skills=filters.show_missing_skills,
                show_feedback=True,
                evidence_map=st.session_state.evidence_map,
                metadata_db=metadata_db,
                min_score=filters.min_score,
            )
        
        with tab_skills:
            # Skill gap analysis
            resume_skills = resume_data.get("skills", [])
            render_skill_gap_full(results, resume_skills)
        
        with tab_saved:
            # Saved jobs section
            saved_jobs = render_saved_jobs_section(results)
            if saved_jobs:
                st.success(f"You have {len(saved_jobs)} saved jobs ready to apply!")
        
        with tab_metrics:
            # Evaluation metrics
            st.subheader("Recommendation Quality Metrics")
            
            # Get user feedback for metrics
            from app.components.feedback import get_feedback_for_job
            user_labels = {}
            for job in results:
                label = get_feedback_for_job(job.job.id)
                if label is not None:
                    user_labels[job.job.id] = label
            
            metrics = evaluate_recommendations(results, user_labels)
            
            # Display metrics in columns
            metrics_display = render_metrics_summary(metrics)
            
            cols = st.columns(3)
            for i, (name, value) in enumerate(metrics_display.items()):
                with cols[i % 3]:
                    st.metric(name, value)
            
            # Text summary
            with st.expander("Full Metrics Report"):
                st.text(metrics.summary())
    
    elif has_resume:
        # Resume loaded but no search yet
        st.info(
            "Resume loaded! Click **Find Matching Jobs** in the sidebar to search."
        )
    
    else:
        # No resume
        st.info(
            "Upload your resume in the sidebar to get started. "
            "You can either upload a PDF or paste the text directly."
        )
        
        # Show sample of available jobs
        st.subheader("Sample Jobs in Database")
        try:
            sample_jobs = metadata_db.get_all_jobs(limit=5)
            if sample_jobs:
                for job in sample_jobs:
                    with st.expander(f"{job.title} @ {job.company}"):
                        st.caption(f"Location: {job.location}")
                        st.caption(f"Posted: {job.posted_at.strftime('%Y-%m-%d')}")
                        desc = job.description[:300] + "..." if len(job.description) > 300 else job.description
                        st.text(desc)
                        st.markdown(f"[View Posting]({job.url})")
            else:
                st.caption("No jobs in database yet.")
        except Exception as e:
            st.caption(f"Could not load sample jobs: {e}")


if __name__ == "__main__":
    main()
