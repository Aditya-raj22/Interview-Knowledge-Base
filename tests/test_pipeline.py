"""Integration tests for the full pipeline."""
from models import InterviewContext
import ingestion
import indexing
import generation


def test_full_pipeline_integration():
    """Test that the full pipeline runs end-to-end."""
    # Step 1: Create context
    context = InterviewContext(
        company="TestCorp",
        person="Test Person",
        role="Test Role"
    )

    # Step 2: Ingest
    documents = ingestion.main(context)
    assert len(documents) > 0

    # Step 3: Index
    chunks = indexing.main(documents)
    assert len(chunks) > 0

    # Step 4: Generate
    response = generation.main("What is the test about?", chunks)
    assert isinstance(response, str)
    assert len(response) > 0


def test_pipeline_data_flow():
    """Test that data flows correctly through pipeline stages."""
    context = InterviewContext(company="A", person="B", role="C")

    # Ingestion output becomes indexing input
    docs = ingestion.main(context)
    chunks = indexing.main(docs)

    # Indexing output becomes generation input
    result = generation.main("test query", chunks)

    # Verify types at each stage
    from models import Document, VectorChunk
    assert all(isinstance(d, Document) for d in docs)
    assert all(isinstance(c, VectorChunk) for c in chunks)
    assert isinstance(result, str)
