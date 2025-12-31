"""Matching module for embeddings, scoring, and evidence extraction."""

from src.matching.embeddings import (
    EmbeddingConfig,
    EmbeddingManager,
    compute_version_id,
)
from src.matching.scorer import (
    HybridScorer,
    ResumeProfile,
    ScoredJob,
    ScoreBreakdown,
    ScoringWeights,
)
from src.matching.evidence import (
    EvidenceExtractor,
    EvidenceMatch,
    EvidenceResult,
    highlight_text,
)

__all__ = [
    # Embeddings
    "EmbeddingConfig",
    "EmbeddingManager",
    "compute_version_id",
    # Scorer
    "HybridScorer",
    "ResumeProfile",
    "ScoredJob",
    "ScoreBreakdown",
    "ScoringWeights",
    # Evidence
    "EvidenceExtractor",
    "EvidenceMatch",
    "EvidenceResult",
    "highlight_text",
]
