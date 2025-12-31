"""Skill gap visualization component for Streamlit."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from src.matching.scorer import ScoredJob


@dataclass
class SkillGapAnalysis:
    """Analysis of skill gaps across job recommendations."""
    
    resume_skills: list[str]
    all_required_skills: Counter  # skill -> count of jobs requiring it
    matched_skills: Counter  # skill -> count of jobs where it matched
    missing_skills: Counter  # skill -> count of jobs where it's missing
    
    @property
    def coverage_rate(self) -> float:
        """Percentage of required skills covered by resume."""
        total_required = sum(self.all_required_skills.values())
        total_matched = sum(self.matched_skills.values())
        if total_required == 0:
            return 1.0
        return total_matched / total_required
    
    @property
    def top_missing_skills(self) -> list[tuple[str, int]]:
        """Top skills missing from resume, sorted by frequency."""
        return self.missing_skills.most_common(10)
    
    @property
    def top_matched_skills(self) -> list[tuple[str, int]]:
        """Top skills matched from resume, sorted by frequency."""
        return self.matched_skills.most_common(10)
    
    @property
    def high_impact_gaps(self) -> list[str]:
        """Skills that appear in many jobs but are missing from resume."""
        # Skills missing in 3+ jobs
        return [skill for skill, count in self.missing_skills.items() if count >= 3]


def analyze_skill_gaps(
    scored_jobs: list["ScoredJob"],
    resume_skills: list[str],
) -> SkillGapAnalysis:
    """
    Analyze skill gaps across a list of scored jobs.
    
    Args:
        scored_jobs: List of scored job results
        resume_skills: List of skills from resume
        
    Returns:
        SkillGapAnalysis with aggregated skill data
    """
    all_required: Counter = Counter()
    matched: Counter = Counter()
    missing: Counter = Counter()
    
    for job in scored_jobs:
        # Count all skills from matched + missing
        job_skills = set(job.matched_skills) | set(job.missing_skills)
        for skill in job_skills:
            all_required[skill] += 1
        
        # Count matched
        for skill in job.matched_skills:
            matched[skill] += 1
        
        # Count missing
        for skill in job.missing_skills:
            missing[skill] += 1
    
    return SkillGapAnalysis(
        resume_skills=list(resume_skills),
        all_required_skills=all_required,
        matched_skills=matched,
        missing_skills=missing,
    )


def render_skill_gap_summary(analysis: SkillGapAnalysis) -> None:
    """
    Render a summary of skill gaps.
    
    Args:
        analysis: SkillGapAnalysis object
    """
    st.subheader("Skill Gap Analysis")
    
    # Coverage metric
    coverage = analysis.coverage_rate
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Skill Coverage",
            f"{coverage:.0%}",
            help="Percentage of job-required skills covered by your resume",
        )
    
    with col2:
        st.metric(
            "Skills Matched",
            len(analysis.matched_skills),
            help="Number of unique skills matched across all jobs",
        )
    
    with col3:
        st.metric(
            "Skills to Learn",
            len(analysis.missing_skills),
            help="Number of unique skills missing from your resume",
        )


def render_skill_gap_chart(analysis: SkillGapAnalysis) -> None:
    """
    Render a visual chart of skill gaps.
    
    Args:
        analysis: SkillGapAnalysis object
    """
    # Top matched skills
    st.markdown("### Your Strongest Skills")
    
    top_matched = analysis.top_matched_skills
    if top_matched:
        for skill, count in top_matched:
            # Progress bar based on count
            max_count = top_matched[0][1] if top_matched else 1
            progress = count / max_count
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(progress, text=skill)
            with col2:
                st.caption(f"{count} jobs")
    else:
        st.caption("No skill matches found.")
    
    st.markdown("---")
    
    # Top missing skills (gaps)
    st.markdown("### Skills to Develop")
    
    top_missing = analysis.top_missing_skills
    if top_missing:
        for skill, count in top_missing:
            max_count = top_missing[0][1] if top_missing else 1
            progress = count / max_count
            
            col1, col2 = st.columns([3, 1])
            with col1:
                # Red-tinted progress for missing skills
                st.progress(progress, text=skill)
            with col2:
                st.caption(f"{count} jobs")
        
        # High impact recommendations
        high_impact = analysis.high_impact_gaps
        if high_impact:
            st.info(
                f"**High Impact:** Learning **{', '.join(high_impact[:3])}** "
                f"would improve your match for {len(high_impact)} or more jobs."
            )
    else:
        st.success("Great! You have all the skills for these jobs.")


def render_skill_comparison(
    analysis: SkillGapAnalysis,
    expanded: bool = False,
) -> None:
    """
    Render a side-by-side comparison of matched vs missing skills.
    
    Args:
        analysis: SkillGapAnalysis object
        expanded: Whether to expand by default
    """
    with st.expander("Detailed Skill Comparison", expanded=expanded):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Matched Skills")
            if analysis.matched_skills:
                skill_html = " ".join(
                    f'<span style="background-color: #d4edda; color: #155724; '
                    f'padding: 4px 10px; border-radius: 15px; margin: 3px; '
                    f'display: inline-block; font-size: 0.9em;">'
                    f'{skill} ({count})</span>'
                    for skill, count in analysis.top_matched_skills
                )
                st.markdown(skill_html, unsafe_allow_html=True)
            else:
                st.caption("None")
        
        with col2:
            st.markdown("#### Missing Skills")
            if analysis.missing_skills:
                skill_html = " ".join(
                    f'<span style="background-color: #f8d7da; color: #721c24; '
                    f'padding: 4px 10px; border-radius: 15px; margin: 3px; '
                    f'display: inline-block; font-size: 0.9em;">'
                    f'{skill} ({count})</span>'
                    for skill, count in analysis.top_missing_skills
                )
                st.markdown(skill_html, unsafe_allow_html=True)
            else:
                st.caption("None")


def render_skill_gap_full(
    scored_jobs: list["ScoredJob"],
    resume_skills: list[str],
) -> SkillGapAnalysis | None:
    """
    Render the complete skill gap analysis section.
    
    Args:
        scored_jobs: List of scored jobs
        resume_skills: Skills from resume
        
    Returns:
        SkillGapAnalysis if jobs were provided
    """
    if not scored_jobs:
        st.info("Search for jobs to see skill gap analysis.")
        return None
    
    analysis = analyze_skill_gaps(scored_jobs, resume_skills)
    
    render_skill_gap_summary(analysis)
    st.divider()
    render_skill_gap_chart(analysis)
    render_skill_comparison(analysis)
    
    return analysis


def render_single_job_skills(
    matched_skills: list[str],
    missing_skills: list[str],
) -> None:
    """
    Render skill analysis for a single job.
    
    Args:
        matched_skills: Skills matched for this job
        missing_skills: Skills missing for this job
    """
    if matched_skills:
        coverage = len(matched_skills) / (len(matched_skills) + len(missing_skills))
        st.progress(coverage, text=f"Skill Match: {coverage:.0%}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if matched_skills:
            st.markdown("**You have:**")
            skill_html = " ".join(
                f'<span style="background-color: #d4edda; color: #155724; '
                f'padding: 2px 8px; border-radius: 12px; margin: 2px; '
                f'display: inline-block; font-size: 0.85em;">{skill}</span>'
                for skill in sorted(matched_skills)
            )
            st.markdown(skill_html, unsafe_allow_html=True)
    
    with col2:
        if missing_skills:
            st.markdown("**To learn:**")
            skill_html = " ".join(
                f'<span style="background-color: #fff3cd; color: #856404; '
                f'padding: 2px 8px; border-radius: 12px; margin: 2px; '
                f'display: inline-block; font-size: 0.85em;">{skill}</span>'
                for skill in sorted(missing_skills)
            )
            st.markdown(skill_html, unsafe_allow_html=True)
