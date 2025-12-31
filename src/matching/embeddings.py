"""Embedding generation and management for semantic search."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

import numpy as np

from src.processing.text_cleaner import CLEANING_VERSION
from src.utils.config import get_settings
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = get_logger(__name__)


@dataclass(frozen=True)
class EmbeddingConfig:
    """Configuration and metadata for embeddings."""

    model_name: str
    embedding_dim: int
    version_id: str  # Unique identifier for this model + cleaning version

    def __str__(self) -> str:
        return f"EmbeddingConfig(model={self.model_name}, dim={self.embedding_dim}, version={self.version_id})"


def compute_version_id(model_name: str, cleaning_version: str = CLEANING_VERSION) -> str:
    """
    Compute a stable version identifier for embeddings.

    Combines model name and cleaning version to detect when
    embeddings need to be regenerated.

    Args:
        model_name: Name of the embedding model
        cleaning_version: Version of text cleaning logic

    Returns:
        Short hash string (12 chars)
    """
    version_string = f"{model_name}|cleaning_v{cleaning_version}"
    return hashlib.sha1(version_string.encode()).hexdigest()[:12]


class EmbeddingManager:
    """
    Manages embedding model loading and text encoding.

    Uses lazy loading to avoid loading the model until needed.
    Supports batched encoding for performance.
    """

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
    ):
        """
        Initialize the embedding manager.

        Args:
            model_name: HuggingFace model name (defaults to config)
            device: Device to use ('cpu', 'cuda', 'mps', or None for auto)
        """
        settings = get_settings()
        self._model_name = model_name or settings.embedding_model_name
        self._device = device
        self._model: "SentenceTransformer | None" = None
        self._embedding_dim: int | None = None

    def _load_model(self) -> "SentenceTransformer":
        """Lazy load the embedding model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self._model_name}")
            self._model = SentenceTransformer(self._model_name, device=self._device)
            self._embedding_dim = self._model.get_sentence_embedding_dimension()
            logger.info(
                f"Model loaded: dim={self._embedding_dim}, device={self._model.device}"
            )
        return self._model

    @property
    def model(self) -> "SentenceTransformer":
        """Get the loaded model (loads if not already loaded)."""
        return self._load_model()

    def config(self) -> EmbeddingConfig:
        """Get the embedding configuration."""
        # Ensure model is loaded to get dimension
        self._load_model()
        return EmbeddingConfig(
            model_name=self._model_name,
            embedding_dim=self._embedding_dim or 384,  # fallback
            version_id=compute_version_id(self._model_name),
        )

    def embed_texts(
        self,
        texts: Sequence[str],
        *,
        batch_size: int = 64,
        normalize: bool = True,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Embed multiple texts into vectors.

        Args:
            texts: Sequence of texts to embed
            batch_size: Batch size for encoding (adjust for memory)
            normalize: Whether to L2-normalize embeddings
            show_progress: Show progress bar during encoding

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            dim = self._embedding_dim or 384
            return np.array([]).reshape(0, dim)

        model = self._load_model()

        logger.debug(f"Embedding {len(texts)} texts with batch_size={batch_size}")

        embeddings = model.encode(
            list(texts),
            batch_size=batch_size,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
            show_progress_bar=show_progress,
        )

        return embeddings

    def embed_text(self, text: str, *, normalize: bool = True) -> np.ndarray:
        """
        Embed a single text into a vector.

        Args:
            text: Text to embed
            normalize: Whether to L2-normalize the embedding

        Returns:
            numpy array of shape (embedding_dim,)
        """
        embeddings = self.embed_texts([text], normalize=normalize)
        return embeddings[0]

    def compute_similarity(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray,
    ) -> np.ndarray:
        """
        Compute cosine similarity between query and documents.

        Args:
            query_embedding: Single query embedding (embedding_dim,)
            document_embeddings: Document embeddings (n_docs, embedding_dim)

        Returns:
            Similarity scores (n_docs,)
        """
        # If embeddings are normalized, cosine similarity = dot product
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        similarities = np.dot(document_embeddings, query_embedding.T).flatten()
        return similarities

    def unload_model(self) -> None:
        """Unload the model to free memory."""
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("Embedding model unloaded")
