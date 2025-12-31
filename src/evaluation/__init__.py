"""Evaluation module for recommendation quality metrics."""

from src.evaluation.metrics import (
    EvaluationMetrics,
    evaluate_recommendations,
    render_metrics_summary,
    precision_at_k,
    compute_diversity,
)

__all__ = [
    "EvaluationMetrics",
    "evaluate_recommendations",
    "render_metrics_summary",
    "precision_at_k",
    "compute_diversity",
]
