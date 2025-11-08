"""Shared pytest fixtures for all tests."""
import pytest
from models import InterviewContext, Document, VectorChunk


@pytest.fixture
def sample_context():
    """Provide a sample interview context."""
    return InterviewContext(
        company="TestCompany",
        person="John Doe",
        role="CTO"
    )


@pytest.fixture
def sample_documents():
    """Provide sample documents."""
    return [
        Document(
            content="Sample content about leadership and technology.",
            source="https://example.com/article1",
            metadata={"type": "blog"}
        ),
        Document(
            content="Interview discussing innovation and team building.",
            source="https://example.com/article2",
            metadata={"type": "interview"}
        ),
    ]


@pytest.fixture
def sample_chunks():
    """Provide sample vector chunks."""
    return [
        VectorChunk(
            text="Leadership and technology insights.",
            embedding=[0.1] * 384,  # Mock embedding
            doc_id="doc1#0",
            entities=["Leadership"]
        ),
        VectorChunk(
            text="Innovation and team building strategies.",
            embedding=[0.2] * 384,
            doc_id="doc2#0",
            entities=["Innovation"]
        ),
    ]
