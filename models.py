"""Shared data models for the Interview Knowledge Base."""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class InterviewContext:
    """Context for an interview preparation session."""
    company: str
    person: str
    role: str = ""  # Optional role/position


@dataclass
class Document:
    """A source document retrieved during ingestion."""
    content: str
    source: str  # URL, file path, or source identifier
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorChunk:
    """A text chunk with its vector embedding."""
    text: str
    embedding: List[float]
    doc_id: str  # Reference to source document
    entities: List[str] = field(default_factory=list)  # NER entities
