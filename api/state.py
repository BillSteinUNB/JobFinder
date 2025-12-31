"""Shared application state for the FastAPI app."""

from pathlib import Path
from typing import TYPE_CHECKING

from src.db.metadata_db import MetadataDB
from src.db.vector_db import VectorDB
from src.matching.embeddings import EmbeddingManager
from src.matching.scorer import HybridScorer, ResumeProfile
from src.processing.text_cleaner import clean_resume_text, extract_skills_simple
from src.utils.config import get_settings
from src.utils.logger import get_logger

if TYPE_CHECKING:
    import numpy as np

logger = get_logger(__name__)


class AppState:
    """
    Shared application state.
    
    Holds database connections, embedding manager, and current resume profile.
    Initialized once at startup and shared across requests.
    """

    def __init__(self) -> None:
        """Initialize application state with lazy-loaded components."""
        self._settings = get_settings()
        self._metadata_db: MetadataDB | None = None
        self._vector_db: VectorDB | None = None
        self._embedding_manager: EmbeddingManager | None = None
        self._scorer: HybridScorer | None = None
        self._resume_profile: ResumeProfile | None = None
        
        logger.info("AppState initialized")

    @property
    def metadata_db(self) -> MetadataDB:
        """Get or create the metadata database connection."""
        if self._metadata_db is None:
            self._metadata_db = MetadataDB()
        return self._metadata_db

    @property
    def embedding_manager(self) -> EmbeddingManager:
        """Get or create the embedding manager."""
        if self._embedding_manager is None:
            self._embedding_manager = EmbeddingManager()
        return self._embedding_manager

    @property
    def vector_db(self) -> VectorDB:
        """Get or create the vector database connection."""
        if self._vector_db is None:
            config = self.embedding_manager.config()
            self._vector_db = VectorDB(embedding_version=config.version_id)
        return self._vector_db

    @property
    def scorer(self) -> HybridScorer:
        """Get or create the hybrid scorer."""
        if self._scorer is None:
            self._scorer = HybridScorer()
        return self._scorer

    @property
    def resume_profile(self) -> ResumeProfile | None:
        """Get the current resume profile (if uploaded)."""
        return self._resume_profile

    def set_resume_profile(self, profile: ResumeProfile) -> None:
        """Set the current resume profile."""
        self._resume_profile = profile
        logger.info(f"Resume profile set: {len(profile.skills)} skills extracted")

    def create_resume_profile(
        self,
        raw_text: str,
        preferred_location: str | None = None,
        min_salary: float | None = None,
    ) -> ResumeProfile:
        """
        Create a resume profile from raw text.
        
        Args:
            raw_text: Raw resume text
            preferred_location: User's preferred job location
            min_salary: User's minimum desired salary
            
        Returns:
            ResumeProfile with extracted skills and embedding
        """
        clean_result = clean_resume_text(raw_text)
        skills = set(extract_skills_simple(raw_text))
        embedding = self.embedding_manager.embed_text(clean_result.text)
        
        profile = ResumeProfile(
            raw_text=raw_text,
            clean_text=clean_result.text,
            skills=skills,
            embedding=embedding.tolist(),
            preferred_location=preferred_location,
            min_salary=min_salary,
        )
        
        self.set_resume_profile(profile)
        return profile

    def cleanup(self) -> None:
        """Cleanup resources on shutdown."""
        if self._embedding_manager is not None:
            self._embedding_manager.unload_model()
        logger.info("AppState cleanup complete")
