"""Integration tests for full pipeline orchestration."""
import json
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from main import run_pipeline


@patch('ingestion.run_ingestion')
@patch('indexing.build_index')
@patch('generation.generate_brief')
def test_full_pipeline_integration(mock_generate, mock_build_index, mock_run_ingestion, tmp_path):
    """Test that full pipeline runs with all three steps."""
    # Setup mocks
    mock_run_ingestion.return_value = tmp_path / "raw" / "testcompany" / "source.jsonl"
    mock_build_index.return_value = tmp_path / "index" / "testcompany"
    mock_generate.return_value = {
        "summary": "Mock brief",
        "insights": [{"text": "Insight 1", "citations": ["test#0#0"]}],
        "key_entities": [{"type": "PERSON", "text": "John", "mentions": 2}],
        "citations": ["test#0#0"],
        "metadata": {
            "company": "testcompany",
            "mode": "summary",
            "model": "gpt-4o",
            "retrieval_time_ms": 100,
            "generation_time_ms": 500,
            "total_time_ms": 600,
        }
    }

    # Run pipeline
    results = run_pipeline(
        company="TestCompany",
        person="John Doe",
        mode="summary",
    )

    # Assert all steps succeeded
    assert results["company"] == "TestCompany"
    assert results["person"] == "John Doe"
    assert results["mode"] == "summary"

    assert "ingestion" in results["steps"]
    assert results["steps"]["ingestion"]["status"] == "success"

    assert "indexing" in results["steps"]
    assert results["steps"]["indexing"]["status"] == "success"

    assert "generation" in results["steps"]
    assert results["steps"]["generation"]["status"] == "success"

    # Verify mocks were called correctly
    mock_run_ingestion.assert_called_once_with("TestCompany", "John Doe")
    mock_build_index.assert_called_once_with("testcompany")
    mock_generate.assert_called_once()


@patch('ingestion.run_ingestion')
@patch('indexing.build_index')
@patch('generation.generate_brief')
def test_pipeline_data_flow(mock_generate, mock_build_index, mock_run_ingestion, tmp_path):
    """Test that output of each step feeds into the next."""
    # Setup file paths
    ingestion_output = tmp_path / "raw" / "testcompany" / "source.jsonl"
    index_output = tmp_path / "index" / "testcompany"

    mock_run_ingestion.return_value = ingestion_output
    mock_build_index.return_value = index_output
    mock_generate.return_value = {
        "summary": "Test",
        "insights": [],
        "key_entities": [],
        "citations": [],
        "metadata": {}
    }

    # Run pipeline
    results = run_pipeline(company="TestCompany", person="John")

    # Verify data flow
    # Step 1: Ingestion output path is stored
    assert results["steps"]["ingestion"]["output_file"] == str(ingestion_output)

    # Step 2: Indexing uses company folder derived from ingestion
    mock_build_index.assert_called_with("testcompany")
    assert results["steps"]["indexing"]["index_dir"] == str(index_output)

    # Step 3: Generation uses same company folder
    gen_call_args = mock_generate.call_args
    assert gen_call_args[1]["company"] == "testcompany"
    assert gen_call_args[1]["person"] == "John"


@patch('ingestion.run_ingestion')
def test_pipeline_fails_on_ingestion_error(mock_run_ingestion):
    """Test that pipeline stops if ingestion fails."""
    mock_run_ingestion.side_effect = Exception("Ingestion failed")

    results = run_pipeline(company="TestCompany")

    assert results["steps"]["ingestion"]["status"] == "failed"
    assert "error" in results["steps"]["ingestion"]
    assert "indexing" not in results["steps"]
    assert "generation" not in results["steps"]


@patch('ingestion.run_ingestion')
@patch('indexing.build_index')
def test_pipeline_fails_on_indexing_error(mock_build_index, mock_run_ingestion, tmp_path):
    """Test that pipeline stops if indexing fails."""
    mock_run_ingestion.return_value = tmp_path / "raw" / "testcompany" / "source.jsonl"
    mock_build_index.side_effect = Exception("Indexing failed")

    results = run_pipeline(company="TestCompany")

    assert results["steps"]["ingestion"]["status"] == "success"
    assert results["steps"]["indexing"]["status"] == "failed"
    assert "error" in results["steps"]["indexing"]
    assert "generation" not in results["steps"]


@patch('ingestion.run_ingestion')
@patch('indexing.build_index')
@patch('generation.generate_brief')
def test_pipeline_fails_on_generation_error(mock_generate, mock_build_index, mock_run_ingestion, tmp_path):
    """Test that pipeline handles generation errors."""
    mock_run_ingestion.return_value = tmp_path / "raw" / "testcompany" / "source.jsonl"
    mock_build_index.return_value = tmp_path / "index" / "testcompany"
    mock_generate.side_effect = Exception("Generation failed")

    results = run_pipeline(company="TestCompany")

    assert results["steps"]["ingestion"]["status"] == "success"
    assert results["steps"]["indexing"]["status"] == "success"
    assert results["steps"]["generation"]["status"] == "failed"
    assert "error" in results["steps"]["generation"]


@patch('indexing.build_index')
@patch('generation.generate_brief')
def test_pipeline_skip_ingestion(mock_generate, mock_build_index, tmp_path):
    """Test that pipeline can skip ingestion."""
    mock_build_index.return_value = tmp_path / "index" / "testcompany"
    mock_generate.return_value = {
        "summary": "Test",
        "insights": [],
        "key_entities": [],
        "citations": [],
        "metadata": {}
    }

    results = run_pipeline(company="TestCompany", skip_ingestion=True)

    assert results["steps"]["ingestion"]["status"] == "skipped"
    assert results["steps"]["indexing"]["status"] == "success"
    assert results["steps"]["generation"]["status"] == "success"


@patch('generation.generate_brief')
def test_pipeline_skip_ingestion_and_indexing(mock_generate):
    """Test that pipeline can skip both ingestion and indexing."""
    mock_generate.return_value = {
        "summary": "Test",
        "insights": [],
        "key_entities": [],
        "citations": [],
        "metadata": {}
    }

    results = run_pipeline(
        company="TestCompany",
        skip_ingestion=True,
        skip_indexing=True
    )

    assert results["steps"]["ingestion"]["status"] == "skipped"
    assert results["steps"]["indexing"]["status"] == "skipped"
    assert results["steps"]["generation"]["status"] == "success"


@patch('ingestion.run_ingestion')
@patch('indexing.build_index')
@patch('generation.generate_brief')
def test_pipeline_with_different_modes(mock_generate, mock_build_index, mock_run_ingestion, tmp_path):
    """Test that pipeline works with different generation modes."""
    mock_run_ingestion.return_value = tmp_path / "raw" / "testcompany" / "source.jsonl"
    mock_build_index.return_value = tmp_path / "index" / "testcompany"
    mock_generate.return_value = {
        "summary": "Test",
        "insights": [],
        "key_entities": [],
        "citations": [],
        "metadata": {}
    }

    modes = ["summary", "technical", "biographical", "strategic"]

    for mode in modes:
        results = run_pipeline(company="TestCompany", mode=mode)

        assert results["mode"] == mode
        assert results["steps"]["generation"]["status"] == "success"

        # Verify generate_brief was called with correct mode
        gen_call_args = mock_generate.call_args
        assert gen_call_args[1]["mode"] == mode


@patch('ingestion.run_ingestion')
@patch('indexing.build_index')
@patch('generation.generate_brief')
def test_pipeline_output_structure(mock_generate, mock_build_index, mock_run_ingestion, tmp_path):
    """Test that pipeline output has correct structure."""
    mock_run_ingestion.return_value = tmp_path / "raw" / "testcompany" / "source.jsonl"
    mock_build_index.return_value = tmp_path / "index" / "testcompany"
    mock_generate.return_value = {
        "summary": "Generated brief text",
        "insights": [
            {"text": "Insight 1", "citations": ["test#0#0"]},
            {"text": "Insight 2", "citations": ["test#1#0"]}
        ],
        "key_entities": [
            {"type": "PERSON", "text": "John Doe", "mentions": 3},
            {"type": "ORG", "text": "TechCorp", "mentions": 5}
        ],
        "citations": ["test#0#0", "test#1#0"],
        "metadata": {
            "company": "testcompany",
            "mode": "summary",
            "model": "gpt-4o",
            "n_chunks_retrieved": 5,
            "n_citations": 2,
            "retrieval_time_ms": 150,
            "generation_time_ms": 800,
            "total_time_ms": 950,
        }
    }

    results = run_pipeline(company="TestCompany", person="John Doe")

    # Verify top-level structure
    assert "company" in results
    assert "person" in results
    assert "mode" in results
    assert "steps" in results

    # Verify steps structure
    assert "ingestion" in results["steps"]
    assert "indexing" in results["steps"]
    assert "generation" in results["steps"]

    # Verify brief structure
    brief = results["steps"]["generation"]["brief"]
    assert "summary" in brief
    assert "insights" in brief
    assert "key_entities" in brief
    assert "citations" in brief
    assert "metadata" in brief

    # Verify data types
    assert isinstance(brief["summary"], str)
    assert isinstance(brief["insights"], list)
    assert isinstance(brief["key_entities"], list)
    assert isinstance(brief["citations"], list)
    assert isinstance(brief["metadata"], dict)
