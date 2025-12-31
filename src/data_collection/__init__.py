"""Data collection module for fetching jobs from external sources."""

from src.data_collection.adzuna_client import AdzunaClient, AdzunaClientError
from src.data_collection.schema import (
    AdzunaJob,
    AdzunaSearchResponse,
    Job,
)

__all__ = [
    "AdzunaClient",
    "AdzunaClientError",
    "AdzunaJob",
    "AdzunaSearchResponse",
    "Job",
]
