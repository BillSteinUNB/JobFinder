"""Evaluation metrics for recommendation quality."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from src.matching.scorer import ScoredJob


@dataclass
class EvaluationMetrics:
    """Container for evaluation metric results."""
    
    # Precision metrics
    precision_at_k: dict[int, float] = field(default_factory=dict)
    
    # Diversity metrics
    company_diversity: float = 0.0
    location_diversity: float = 0.0
    category_diversity: float = 0.0
    
    # Score distribution
    avg_score: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    score_std: float = 0.0
    
    # Coverage
    skill_coverage: float = 0.0
    salary_coverage: float = 0.0
    
    # Feedback-based (if available)
    user_precision: float | None = None  # Precision based on user labels
    
    def summary(self) -> str:
        """Generate a text summary of metrics."""
        lines = ["Evaluation Metrics:"]
        
        if self.precision_at_k:
            for k, p in sorted(self.precision_at_k.items()):
                lines.append(f"  Precision@{k}: {p:.2%}")
        
        lines.append(f"  Company Diversity: {self.company_diversity:.2%}")
        lines.append(f"  Location Diversity: {self.location_diversity:.2%}")
        lines.append(f"  Avg Score: {self.avg_score:.2f}")
        lines.append(f"  Score Range: [{self.min_score:.2f}, {self.max_score:.2f}]")
        
        if self.user_precision is not None:
            lines.append(f"  User Precision: {self.user_precision:.2%}")
        
        return "\n".join(lines)


def compute_diversity(items: Sequence[str]) -> float:
    """
    Compute diversity score using normalized entropy.
    
    Higher = more diverse (more even distribution).
    
    Args:
        items: Sequence of categorical items
        
    Returns:
        Diversity score between 0 and 1
    """
    if not items:
        return 0.0
    
    counter = Counter(items)
    n = len(items)
    
    if n <= 1:
        return 1.0  # Single item is maximally diverse
    
    # Compute entropy
    import math
    entropy = 0.0
    for count in counter.values():
        if count > 0:
            p = count / n
            entropy -= p * math.log2(p)
    
    # Normalize by max entropy (uniform distribution)
    max_entropy = math.log2(len(counter))
    
    if max_entropy == 0:
        return 1.0
    
    return entropy / max_entropy


def precision_at_k(
    scored_jobs: list["ScoredJob"],
    labels: dict[str, int],
    k: int,
) -> float:
    """
    Compute Precision@K based on user labels.
    
    Args:
        scored_jobs: List of scored jobs (in ranked order)
        labels: Dictionary mapping job_id to label (1=relevant, 0=not)
        k: Number of top results to consider
        
    Returns:
        Precision@K score (0 to 1)
    """
    if not scored_jobs or k <= 0:
        return 0.0
    
    top_k = scored_jobs[:k]
    relevant = sum(
        1 for job in top_k
        if labels.get(job.job.id) == 1
    )
    
    return relevant / min(k, len(top_k))


def compute_score_statistics(
    scored_jobs: list["ScoredJob"],
) -> tuple[float, float, float, float]:
    """
    Compute score distribution statistics.
    
    Returns:
        Tuple of (avg, min, max, std)
    """
    if not scored_jobs:
        return 0.0, 0.0, 0.0, 0.0
    
    scores = [j.total_score for j in scored_jobs]
    
    avg = sum(scores) / len(scores)
    min_score = min(scores)
    max_score = max(scores)
    
    # Standard deviation
    if len(scores) > 1:
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        std = variance ** 0.5
    else:
        std = 0.0
    
    return avg, min_score, max_score, std


def compute_skill_coverage(
    scored_jobs: list["ScoredJob"],
) -> float:
    """
    Compute average skill coverage across jobs.
    
    Returns:
        Average fraction of job skills covered by resume
    """
    if not scored_jobs:
        return 0.0
    
    coverages = []
    for job in scored_jobs:
        total_skills = len(job.matched_skills) + len(job.missing_skills)
        if total_skills > 0:
            coverage = len(job.matched_skills) / total_skills
            coverages.append(coverage)
    
    if not coverages:
        return 0.0
    
    return sum(coverages) / len(coverages)


def compute_salary_coverage(
    scored_jobs: list["ScoredJob"],
) -> float:
    """
    Compute fraction of jobs with salary information.
    
    Returns:
        Fraction of jobs with salary data
    """
    if not scored_jobs:
        return 0.0
    
    with_salary = sum(
        1 for job in scored_jobs
        if job.job.salary_min is not None or job.job.salary_max is not None
    )
    
    return with_salary / len(scored_jobs)


def evaluate_recommendations(
    scored_jobs: list["ScoredJob"],
    user_labels: dict[str, int] | None = None,
    k_values: list[int] | None = None,
) -> EvaluationMetrics:
    """
    Compute all evaluation metrics for a set of recommendations.
    
    Args:
        scored_jobs: List of scored jobs (in ranked order)
        user_labels: Optional dictionary of user feedback (job_id -> label)
        k_values: List of K values for Precision@K (default: [5, 10, 20])
        
    Returns:
        EvaluationMetrics with all computed values
    """
    if k_values is None:
        k_values = [5, 10, 20]
    
    metrics = EvaluationMetrics()
    
    if not scored_jobs:
        return metrics
    
    # Precision@K (requires user labels)
    if user_labels:
        for k in k_values:
            metrics.precision_at_k[k] = precision_at_k(scored_jobs, user_labels, k)
        
        # Overall user precision
        labeled_jobs = [j for j in scored_jobs if j.job.id in user_labels]
        if labeled_jobs:
            relevant = sum(1 for j in labeled_jobs if user_labels[j.job.id] == 1)
            metrics.user_precision = relevant / len(labeled_jobs)
    
    # Diversity
    companies = [j.job.company for j in scored_jobs]
    locations = [j.job.location for j in scored_jobs]
    categories = [j.job.category or "Unknown" for j in scored_jobs]
    
    metrics.company_diversity = compute_diversity(companies)
    metrics.location_diversity = compute_diversity(locations)
    metrics.category_diversity = compute_diversity(categories)
    
    # Score statistics
    avg, min_s, max_s, std = compute_score_statistics(scored_jobs)
    metrics.avg_score = avg
    metrics.min_score = min_s
    metrics.max_score = max_s
    metrics.score_std = std
    
    # Coverage
    metrics.skill_coverage = compute_skill_coverage(scored_jobs)
    metrics.salary_coverage = compute_salary_coverage(scored_jobs)
    
    return metrics


def render_metrics_summary(metrics: EvaluationMetrics) -> dict[str, str]:
    """
    Render metrics as display-friendly strings.
    
    Returns:
        Dictionary of metric name -> formatted value
    """
    result = {}
    
    # Precision@K
    for k, p in sorted(metrics.precision_at_k.items()):
        result[f"Precision@{k}"] = f"{p:.0%}"
    
    # Diversity
    result["Company Diversity"] = f"{metrics.company_diversity:.0%}"
    result["Location Diversity"] = f"{metrics.location_diversity:.0%}"
    
    # Scores
    result["Avg Score"] = f"{metrics.avg_score:.2f}"
    result["Score Range"] = f"{metrics.min_score:.2f} - {metrics.max_score:.2f}"
    
    # Coverage
    result["Skill Coverage"] = f"{metrics.skill_coverage:.0%}"
    result["Salary Data"] = f"{metrics.salary_coverage:.0%}"
    
    if metrics.user_precision is not None:
        result["User Approval"] = f"{metrics.user_precision:.0%}"
    
    return result
