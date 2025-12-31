"""Adzuna API client for fetching job postings."""

import math
import time
from typing import Iterator

import requests
from pydantic import ValidationError

from src.data_collection.schema import AdzunaJob, AdzunaSearchResponse, Job
from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AdzunaClientError(Exception):
    """Custom exception for Adzuna API errors."""

    pass


class AdzunaClient:
    """
    Client for the Adzuna Job Search API.

    Handles authentication, pagination, rate limiting, and data validation.
    """

    BASE_URL = "https://api.adzuna.com/v1/api/jobs"
    MAX_RESULTS_PER_PAGE = 50
    DEFAULT_COUNTRY = "us"

    # Rate limiting (free tier: 25 hits/min)
    RATE_LIMIT_DELAY = 2.5  # seconds between requests

    def __init__(
        self,
        app_id: str | None = None,
        app_key: str | None = None,
        country: str = DEFAULT_COUNTRY,
    ):
        """
        Initialize the Adzuna client.

        Args:
            app_id: Adzuna API App ID (defaults to env var)
            app_key: Adzuna API Key (defaults to env var)
            country: Country code for job search (default: 'us')
        """
        settings = get_settings()
        self.app_id = app_id or settings.adzuna_app_id
        self.app_key = app_key or settings.adzuna_app_key
        self.country = country

        if not self.app_id or not self.app_key:
            raise AdzunaClientError(
                "Adzuna API credentials not configured. "
                "Set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env file."
            )

        self._session = requests.Session()
        self._last_request_time: float = 0

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            sleep_time = self.RATE_LIMIT_DELAY - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _build_url(self, page: int = 1) -> str:
        """Build the API URL for a given page."""
        return f"{self.BASE_URL}/{self.country}/search/{page}"

    def _build_params(
        self,
        what: str | None = None,
        what_phrase: str | None = None,
        where: str | None = None,
        max_days_old: int | None = None,
        salary_min: int | None = None,
        salary_max: int | None = None,
        full_time: bool | None = None,
        permanent: bool | None = None,
        sort_by: str = "date",
        results_per_page: int = MAX_RESULTS_PER_PAGE,
    ) -> dict:
        """Build query parameters for the API request."""
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": min(results_per_page, self.MAX_RESULTS_PER_PAGE),
            "content-type": "application/json",
        }

        if what:
            params["what"] = what
        if what_phrase:
            params["what_phrase"] = what_phrase
        if where:
            params["where"] = where
        if max_days_old:
            params["max_days_old"] = max_days_old
        if salary_min:
            params["salary_min"] = salary_min
        if salary_max:
            params["salary_max"] = salary_max
        if full_time is not None:
            params["full_time"] = 1 if full_time else 0
        if permanent is not None:
            params["permanent"] = 1 if permanent else 0
        if sort_by:
            params["sort_by"] = sort_by

        return params

    def search(
        self,
        what: str | None = None,
        what_phrase: str | None = None,
        where: str | None = None,
        max_days_old: int = 7,
        salary_min: int | None = None,
        salary_max: int | None = None,
        full_time: bool | None = None,
        permanent: bool | None = None,
        sort_by: str = "date",
        max_results: int = 100,
    ) -> list[Job]:
        """
        Search for jobs and return normalized Job models.

        Args:
            what: Keywords to search for
            what_phrase: Exact phrase to match
            where: Location to search
            max_days_old: Maximum age of job postings in days
            salary_min: Minimum salary filter
            salary_max: Maximum salary filter
            full_time: Filter for full-time jobs only
            permanent: Filter for permanent positions only
            sort_by: Sort field ('date', 'salary', 'relevance')
            max_results: Maximum number of results to return

        Returns:
            List of normalized Job objects
        """
        jobs: list[Job] = []
        pages_needed = math.ceil(max_results / self.MAX_RESULTS_PER_PAGE)

        params = self._build_params(
            what=what,
            what_phrase=what_phrase,
            where=where,
            max_days_old=max_days_old,
            salary_min=salary_min,
            salary_max=salary_max,
            full_time=full_time,
            permanent=permanent,
            sort_by=sort_by,
        )

        for page in range(1, pages_needed + 1):
            if len(jobs) >= max_results:
                break

            self._rate_limit()
            url = self._build_url(page)

            try:
                logger.info(f"Fetching page {page} from Adzuna API...")
                response = self._session.get(url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                search_response = AdzunaSearchResponse.model_validate(data)

                logger.info(
                    f"Page {page}: Got {len(search_response.results)} jobs "
                    f"(total available: {search_response.count})"
                )

                for adzuna_job in search_response.results:
                    if len(jobs) >= max_results:
                        break
                    jobs.append(Job.from_adzuna(adzuna_job))

                # No more results available
                if len(search_response.results) < self.MAX_RESULTS_PER_PAGE:
                    break

            except requests.exceptions.RequestException as e:
                logger.error(f"HTTP error fetching page {page}: {e}")
                raise AdzunaClientError(f"Failed to fetch jobs: {e}") from e
            except ValidationError as e:
                logger.error(f"Validation error on page {page}: {e}")
                raise AdzunaClientError(f"Invalid API response: {e}") from e

        logger.info(f"Total jobs fetched: {len(jobs)}")
        return jobs

    def search_iter(
        self,
        what: str | None = None,
        what_phrase: str | None = None,
        where: str | None = None,
        max_days_old: int = 7,
        max_pages: int = 10,
        **kwargs,
    ) -> Iterator[Job]:
        """
        Iterate over jobs page by page (memory-efficient for large fetches).

        Yields:
            Job objects one at a time
        """
        params = self._build_params(
            what=what,
            what_phrase=what_phrase,
            where=where,
            max_days_old=max_days_old,
            **kwargs,
        )

        for page in range(1, max_pages + 1):
            self._rate_limit()
            url = self._build_url(page)

            try:
                response = self._session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                search_response = AdzunaSearchResponse.model_validate(data)

                for adzuna_job in search_response.results:
                    yield Job.from_adzuna(adzuna_job)

                if len(search_response.results) < self.MAX_RESULTS_PER_PAGE:
                    break

            except (requests.exceptions.RequestException, ValidationError) as e:
                logger.error(f"Error on page {page}: {e}")
                break
