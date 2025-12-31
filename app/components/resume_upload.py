"""Resume upload and processing component for Streamlit."""

from __future__ import annotations

import hashlib
from io import BytesIO
from typing import TYPE_CHECKING

import streamlit as st

from src.processing.pdf_parser import parse_resume_pdf, parse_resume_text, PDFParseError
from src.processing.text_cleaner import clean_job_text, extract_skills_simple

if TYPE_CHECKING:
    from src.matching.embeddings import EmbeddingManager


def _compute_text_hash(text: str) -> str:
    """Compute a hash of text for caching."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _init_resume_state() -> None:
    """Initialize resume-related session state keys."""
    defaults = {
        "resume_raw_text": "",
        "resume_clean_text": "",
        "resume_skills": [],
        "resume_embedding": None,
        "resume_hash": "",
        "resume_source": "",  # "pdf" or "text"
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def _process_resume_text(
    raw_text: str,
    source: str,
    embedding_manager: "EmbeddingManager | None" = None,
) -> bool:
    """
    Process resume text and update session state.
    
    Args:
        raw_text: Raw resume text
        source: Source type ("pdf" or "text")
        embedding_manager: Optional embedding manager for computing embeddings
        
    Returns:
        True if processing succeeded
    """
    if not raw_text.strip():
        st.warning("Resume text is empty.")
        return False
    
    # Check if we've already processed this exact text
    text_hash = _compute_text_hash(raw_text)
    if text_hash == st.session_state.get("resume_hash", ""):
        return True  # Already processed
    
    # Clean the text
    clean_result = clean_job_text(raw_text)
    clean_text = clean_result.text
    
    # Extract skills
    skills = extract_skills_simple(clean_text)
    
    # Update session state
    st.session_state.resume_raw_text = raw_text
    st.session_state.resume_clean_text = clean_text
    st.session_state.resume_skills = skills
    st.session_state.resume_hash = text_hash
    st.session_state.resume_source = source
    
    # Compute embedding if manager provided
    if embedding_manager is not None:
        with st.spinner("Computing resume embedding..."):
            embedding = embedding_manager.embed_text(clean_text)
            st.session_state.resume_embedding = embedding.tolist()
    else:
        st.session_state.resume_embedding = None
    
    return True


def render_resume_upload(
    embedding_manager: "EmbeddingManager | None" = None,
) -> bool:
    """
    Render the resume upload component.
    
    Provides tabs for PDF upload and text paste.
    Extracts text, cleans it, extracts skills, and optionally computes embedding.
    
    Args:
        embedding_manager: Optional embedding manager for computing embeddings
        
    Returns:
        True if a resume has been loaded and processed
    """
    _init_resume_state()
    
    st.subheader("Resume")
    
    tab_pdf, tab_text = st.tabs(["Upload PDF", "Paste Text"])
    
    with tab_pdf:
        uploaded_file = st.file_uploader(
            "Upload your resume",
            type=["pdf"],
            help="Upload a PDF version of your resume",
            key="resume_pdf_uploader",
        )
        
        if uploaded_file is not None:
            try:
                # Save to temp file for pdfplumber
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                try:
                    parsed = parse_resume_pdf(tmp_path, use_cache=False)
                    if _process_resume_text(parsed.text, "pdf", embedding_manager):
                        st.success(f"Parsed {parsed.page_count} page(s), {parsed.word_count} words")
                finally:
                    os.unlink(tmp_path)
                    
            except PDFParseError as e:
                st.error(f"Failed to parse PDF: {e}")
            except Exception as e:
                st.error(f"Error processing PDF: {e}")
    
    with tab_text:
        text_input = st.text_area(
            "Paste your resume text",
            height=300,
            placeholder="Paste your resume content here...",
            key="resume_text_input",
        )
        
        if st.button("Process Resume Text", key="process_text_btn"):
            if text_input.strip():
                if _process_resume_text(text_input, "text", embedding_manager):
                    st.success("Resume text processed successfully")
            else:
                st.warning("Please paste your resume text first")
    
    # Show extracted info if resume is loaded
    has_resume = bool(st.session_state.get("resume_clean_text", ""))
    
    if has_resume:
        with st.expander("Resume Preview", expanded=False):
            # Show source
            source = st.session_state.get("resume_source", "unknown")
            st.caption(f"Source: {source}")
            
            # Show extracted text preview
            clean_text = st.session_state.resume_clean_text
            preview_length = 500
            if len(clean_text) > preview_length:
                st.text(clean_text[:preview_length] + "...")
            else:
                st.text(clean_text)
            
            st.caption(f"Total: {len(clean_text):,} characters")
        
        # Show extracted skills
        skills = st.session_state.get("resume_skills", [])
        if skills:
            with st.expander(f"Extracted Skills ({len(skills)})", expanded=True):
                # Display as tags
                skill_html = " ".join(
                    f'<span style="background-color: #e1f5fe; padding: 2px 8px; '
                    f'border-radius: 12px; margin: 2px; display: inline-block; '
                    f'font-size: 0.85em;">{skill}</span>'
                    for skill in sorted(skills)
                )
                st.markdown(skill_html, unsafe_allow_html=True)
        
        # Show embedding status
        has_embedding = st.session_state.get("resume_embedding") is not None
        if has_embedding:
            st.caption("Embedding computed")
        else:
            st.caption("Embedding not computed (will compute on search)")
    
    return has_resume


def get_resume_data() -> dict:
    """
    Get the current resume data from session state.
    
    Returns:
        Dictionary with resume_raw_text, resume_clean_text, resume_skills,
        resume_embedding, resume_hash, resume_source
    """
    _init_resume_state()
    return {
        "raw_text": st.session_state.resume_raw_text,
        "clean_text": st.session_state.resume_clean_text,
        "skills": st.session_state.resume_skills,
        "embedding": st.session_state.resume_embedding,
        "hash": st.session_state.resume_hash,
        "source": st.session_state.resume_source,
    }


def clear_resume() -> None:
    """Clear all resume data from session state."""
    st.session_state.resume_raw_text = ""
    st.session_state.resume_clean_text = ""
    st.session_state.resume_skills = []
    st.session_state.resume_embedding = None
    st.session_state.resume_hash = ""
    st.session_state.resume_source = ""
