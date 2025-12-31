"""Filter controls component for Streamlit sidebar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import streamlit as st


@dataclass
class FilterState:
    """Current state of all filter controls."""
    
    top_k: int = 50
    min_score: float = 0.55
    recency_days: int | None = None  # None = all time
    location_text: str = ""
    salary_min: float | None = None
    sources: list[str] | None = None  # None = all sources
    show_explanations: bool = True
    show_missing_skills: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "top_k": self.top_k,
            "min_score": self.min_score,
            "recency_days": self.recency_days,
            "location_text": self.location_text,
            "salary_min": self.salary_min,
            "sources": self.sources,
            "show_explanations": self.show_explanations,
            "show_missing_skills": self.show_missing_skills,
        }


# Recency options mapping
RECENCY_OPTIONS: dict[str, int | None] = {
    "All time": None,
    "Last 7 days": 7,
    "Last 14 days": 14,
    "Last 30 days": 30,
    "Last 60 days": 60,
}


def _init_filter_state() -> None:
    """Initialize filter-related session state keys."""
    defaults = {
        "filter_top_k": 50,
        "filter_min_score": 0.55,
        "filter_recency": "All time",
        "filter_location": "",
        "filter_salary_min": 0,
        "filter_sources": [],
        "filter_show_explanations": True,
        "filter_show_missing_skills": False,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def render_filters(available_sources: list[str] | None = None) -> FilterState:
    """
    Render filter controls in the sidebar.
    
    Args:
        available_sources: List of available job sources for multiselect
        
    Returns:
        FilterState with current filter values
    """
    _init_filter_state()
    
    st.subheader("Filters")
    
    # Results count
    top_k = st.slider(
        "Number of results",
        min_value=10,
        max_value=200,
        value=st.session_state.filter_top_k,
        step=10,
        key="filter_top_k",
        help="Maximum number of job results to display",
    )
    
    # Minimum score threshold
    min_score = st.slider(
        "Minimum match score",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.filter_min_score,
        step=0.05,
        format="%.2f",
        key="filter_min_score",
        help="Only show jobs with match score above this threshold",
    )
    
    # Recency filter
    recency_label = st.selectbox(
        "Posted within",
        options=list(RECENCY_OPTIONS.keys()),
        index=list(RECENCY_OPTIONS.keys()).index(st.session_state.filter_recency),
        key="filter_recency",
        help="Filter jobs by posting date",
    )
    recency_days = RECENCY_OPTIONS[recency_label]
    
    # Location preference
    location_text = st.text_input(
        "Preferred location",
        value=st.session_state.filter_location,
        key="filter_location",
        placeholder="e.g., Remote, New York, London",
        help="Enter your preferred location (boosts matching jobs)",
    )
    
    # Minimum salary
    salary_min = st.number_input(
        "Minimum salary",
        min_value=0,
        max_value=500000,
        value=st.session_state.filter_salary_min,
        step=5000,
        key="filter_salary_min",
        help="Minimum annual salary (USD). Set to 0 to ignore.",
    )
    
    # Source filter (if multiple sources available)
    sources: list[str] | None = None
    if available_sources and len(available_sources) > 1:
        selected_sources = st.multiselect(
            "Job sources",
            options=available_sources,
            default=st.session_state.filter_sources or available_sources,
            key="filter_sources",
            help="Select which job sources to include",
        )
        if selected_sources and len(selected_sources) < len(available_sources):
            sources = selected_sources
    
    st.divider()
    
    # Display options
    st.subheader("Display Options")
    
    show_explanations = st.checkbox(
        "Show match explanations",
        value=st.session_state.filter_show_explanations,
        key="filter_show_explanations",
        help="Display why each job was recommended",
    )
    
    show_missing_skills = st.checkbox(
        "Show missing skills",
        value=st.session_state.filter_show_missing_skills,
        key="filter_show_missing_skills",
        help="Display skills required by the job but not found in your resume",
    )
    
    return FilterState(
        top_k=top_k,
        min_score=min_score,
        recency_days=recency_days,
        location_text=location_text,
        salary_min=salary_min if salary_min > 0 else None,
        sources=sources,
        show_explanations=show_explanations,
        show_missing_skills=show_missing_skills,
    )


def get_filter_state() -> FilterState:
    """
    Get the current filter state from session state.
    
    Returns:
        FilterState with current values
    """
    _init_filter_state()
    
    recency_label = st.session_state.get("filter_recency", "All time")
    recency_days = RECENCY_OPTIONS.get(recency_label)
    
    salary_min = st.session_state.get("filter_salary_min", 0)
    
    sources = st.session_state.get("filter_sources", [])
    
    return FilterState(
        top_k=st.session_state.get("filter_top_k", 50),
        min_score=st.session_state.get("filter_min_score", 0.55),
        recency_days=recency_days,
        location_text=st.session_state.get("filter_location", ""),
        salary_min=salary_min if salary_min > 0 else None,
        sources=sources if sources else None,
        show_explanations=st.session_state.get("filter_show_explanations", True),
        show_missing_skills=st.session_state.get("filter_show_missing_skills", False),
    )


def reset_filters() -> None:
    """Reset all filters to default values."""
    st.session_state.filter_top_k = 50
    st.session_state.filter_min_score = 0.55
    st.session_state.filter_recency = "All time"
    st.session_state.filter_location = ""
    st.session_state.filter_salary_min = 0
    st.session_state.filter_sources = []
    st.session_state.filter_show_explanations = True
    st.session_state.filter_show_missing_skills = False
