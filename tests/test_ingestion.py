"""Tests for ingestion module with mocked network calls."""
import json
import pytest
from unittest.mock import patch, Mock
from pathlib import Path
from models import Document
import ingestion
from ingestion.sources import SECSource, PubMedSource, ClinicalTrialsSource, PatentsSource, YouTubeSource


# Mock responses for each source
@pytest.fixture
def mock_sec_response():
    """Mock SEC EDGAR API response."""
    return Mock(text="10-K filing data", status_code=200)


@pytest.fixture
def mock_pubmed_response():
    """Mock PubMed API response."""
    return {
        "esearchresult": {
            "idlist": ["12345678", "87654321"]
        }
    }


@pytest.fixture
def mock_clinical_trials_response():
    """Mock ClinicalTrials.gov API response."""
    return {
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT12345678",
                        "officialTitle": "Test Clinical Trial"
                    },
                    "descriptionModule": {
                        "briefSummary": "This is a test trial summary."
                    }
                }
            }
        ]
    }


@pytest.fixture
def mock_patents_response():
    """Mock Google Patents API response via SerpAPI."""
    return {
        "organic_results": [
            {
                "title": "Test Patent",
                "patent_id": "US1234567",
                "snippet": "Patent description here",
                "filing_date": "2024-01-01"
            }
        ]
    }


@patch('ingestion.sources.sec.requests.get')
def test_sec_source_fetch(mock_get, mock_sec_response):
    """Test SEC source fetching with mocked network call."""
    mock_get.return_value = mock_sec_response

    source = SECSource()
    results = source.fetch("TestCompany", "John Doe")

    assert isinstance(results, list)
    for result in results:
        assert "source" in result
        assert "date" in result
        assert "text" in result


@patch('ingestion.sources.pubmed.requests.get')
def test_pubmed_source_fetch(mock_get, mock_pubmed_response):
    """Test PubMed source fetching with mocked network call."""
    mock_response = Mock()
    mock_response.json.return_value = mock_pubmed_response
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    source = PubMedSource()
    results = source.fetch("TestCompany", "John Doe")

    assert isinstance(results, list)
    assert len(results) > 0
    for result in results:
        assert "source" in result
        assert "PMID" in result["source"]
        assert "date" in result
        assert "text" in result


@patch('ingestion.sources.clinical_trials.requests.get')
def test_clinical_trials_source_fetch(mock_get, mock_clinical_trials_response):
    """Test ClinicalTrials source fetching with mocked network call."""
    mock_response = Mock()
    mock_response.json.return_value = mock_clinical_trials_response
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    source = ClinicalTrialsSource()
    results = source.fetch("TestCompany", "John Doe")

    assert isinstance(results, list)
    assert len(results) > 0
    for result in results:
        assert "source" in result
        assert "NCT" in result["source"]
        assert "date" in result
        assert "text" in result


@patch('ingestion.sources.patents.requests.get')
def test_patents_source_fetch(mock_get, mock_patents_response):
    """Test Patents source fetching with mocked network call."""
    mock_response = Mock()
    mock_response.json.return_value = mock_patents_response
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Mock API key present
    with patch('ingestion.sources.patents.SERPAPI_KEY', 'test_key'):
        source = PatentsSource()
        results = source.fetch("TestCompany", "John Doe")

        assert isinstance(results, list)
        assert len(results) > 0
        for result in results:
            assert "source" in result
            assert "date" in result
            assert "text" in result


def test_youtube_source_fetch():
    """Test YouTube source (placeholder implementation)."""
    with patch('ingestion.sources.youtube.YOUTUBE_API_KEY', 'test_key'):
        source = YouTubeSource()
        results = source.fetch("TestCompany", "John Doe")

        assert isinstance(results, list)
        for result in results:
            assert "source" in result
            assert "date" in result
            assert "text" in result


@patch('ingestion.collector._fetch_from_source')
def test_run_ingestion_creates_jsonl(mock_fetch, tmp_path):
    """Test that run_ingestion creates JSONL file with correct schema."""
    # Mock fetch results
    mock_fetch.return_value = [
        {"source": "Test Source", "date": "2024-01-01", "text": "Test content"}
    ]

    # Use temporary directory for output
    with patch('ingestion.collector.DATA_DIR', tmp_path):
        output_file = ingestion.run_ingestion("TestCompany", "John Doe")

        # Assert file exists
        assert output_file.exists()
        assert output_file.suffix == ".jsonl"

        # Assert JSONL schema
        with open(output_file, "r") as f:
            for line in f:
                doc = json.loads(line)
                assert "source" in doc
                assert "date" in doc
                assert "text" in doc
                assert isinstance(doc["source"], str)
                assert isinstance(doc["date"], str)
                assert isinstance(doc["text"], str)


def test_ingestion_main_returns_list(sample_context):
    """Test that ingestion main returns a list."""
    with patch('ingestion.collector.run_ingestion') as mock_run:
        # Create temp JSONL file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            json.dump({"source": "test", "date": "2024-01-01", "text": "test content"}, f)
            f.write("\n")
            temp_path = Path(f.name)

        mock_run.return_value = temp_path

        result = ingestion.main(sample_context)
        assert isinstance(result, list)

        # Cleanup
        temp_path.unlink()


def test_ingestion_returns_documents(sample_context):
    """Test that ingestion returns Document objects."""
    with patch('ingestion.collector.run_ingestion') as mock_run:
        # Create temp JSONL file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            json.dump({"source": "test", "date": "2024-01-01", "text": "test content"}, f)
            f.write("\n")
            temp_path = Path(f.name)

        mock_run.return_value = temp_path

        result = ingestion.main(sample_context)
        assert len(result) > 0
        assert all(isinstance(doc, Document) for doc in result)

        # Cleanup
        temp_path.unlink()


def test_document_has_required_fields(sample_context):
    """Test that documents have content, source, and metadata."""
    with patch('ingestion.collector.run_ingestion') as mock_run:
        # Create temp JSONL file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            json.dump({"source": "test", "date": "2024-01-01", "text": "test content"}, f)
            f.write("\n")
            temp_path = Path(f.name)

        mock_run.return_value = temp_path

        result = ingestion.main(sample_context)
        for doc in result:
            assert hasattr(doc, 'content')
            assert hasattr(doc, 'source')
            assert hasattr(doc, 'metadata')
            assert isinstance(doc.content, str)
            assert isinstance(doc.source, str)
            assert isinstance(doc.metadata, dict)

        # Cleanup
        temp_path.unlink()
