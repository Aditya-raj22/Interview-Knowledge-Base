"""Data source plugins for ingestion."""
from .base import DataSource
from .sec import SECSource
from .pubmed import PubMedSource
from .clinical_trials import ClinicalTrialsSource
from .patents import PatentsSource
from .youtube import YouTubeSource

# All available sources
ALL_SOURCES = [
    SECSource,
    PubMedSource,
    ClinicalTrialsSource,
    PatentsSource,
    YouTubeSource,
]

__all__ = [
    "DataSource",
    "SECSource",
    "PubMedSource",
    "ClinicalTrialsSource",
    "PatentsSource",
    "YouTubeSource",
    "ALL_SOURCES",
]
