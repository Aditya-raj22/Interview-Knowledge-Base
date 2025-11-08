"""Indexing module for embeddings and NER."""
from .vectorizer import main
from .builder import build_index

__all__ = ["main", "build_index"]
