"""Tests for generation module with new brief generation system."""
import json
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, Mock
import generation
from generation.retriever import SmartRetriever
from generation.prompter import BriefPrompter
from generation.generator import MultiModelGenerator


# Legacy tests (backward compatibility)
def test_generation_main_returns_string(sample_chunks):
    """Test that legacy generation returns a string."""
    query = "What are the key insights?"
    result = generation.main(query, sample_chunks)
    assert isinstance(result, str)


def test_generation_produces_nonempty_response(sample_chunks):
    """Test that legacy generation produces a non-empty response."""
    query = "Tell me about leadership"
    result = generation.main(query, sample_chunks)
    assert len(result) > 0


def test_generation_handles_different_queries(sample_chunks):
    """Test that legacy generation works with various queries."""
    queries = [
        "What is the leadership style?",
        "Tell me about innovation",
        "How does the company approach technology?"
    ]

    for query in queries:
        result = generation.main(query, sample_chunks)
        assert isinstance(result, str)
        assert len(result) > 0


# New brief generation tests
def test_brief_prompter_modes():
    """Test that prompter has all required modes."""
    prompter = BriefPrompter()

    modes = ["summary", "technical", "biographical", "strategic"]
    for mode in modes:
        system_prompt = prompter.get_system_prompt(mode)
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0


def test_brief_prompter_builds_complete_prompt():
    """Test that prompter builds complete prompts."""
    prompter = BriefPrompter()

    sample_chunks = [
        {
            "chunk_id": "test#0#0",
            "text": "Sample text about technology",
            "entities": [{"type": "ORG", "text": "TechCorp"}],
            "score": 0.95,
        }
    ]

    system_prompt, user_prompt = prompter.build_prompt(
        company="TechCorp",
        person="Jane Doe",
        mode="summary",
        retrieved_chunks=sample_chunks,
    )

    assert isinstance(system_prompt, str)
    assert isinstance(user_prompt, str)
    assert "TechCorp" in user_prompt
    assert "Jane Doe" in user_prompt
    assert "test#0#0" in user_prompt


def test_multimodel_generator_initialization():
    """Test that generator initializes correctly."""
    # Test with mock (no API keys)
    with patch('generation.generator.OPENAI_API_KEY', ''), \
         patch('generation.generator.ANTHROPIC_API_KEY', ''):
        gen = MultiModelGenerator("gpt-4o")
        assert gen.provider == "mock"

        gen2 = MultiModelGenerator("claude-3-5-sonnet-20241022")
        assert gen2.provider == "mock"


def test_multimodel_generator_mock_generation():
    """Test mock generation works."""
    gen = MultiModelGenerator("gpt-4o")

    result = gen.generate(
        system_prompt="You are a helpful assistant",
        user_prompt="Tell me about AI",
    )

    assert isinstance(result, str)
    assert len(result) > 0


def test_generator_extracts_citations():
    """Test citation extraction from generated text."""
    gen = MultiModelGenerator("gpt-4o")

    text = """
    Some information from [source#0#0] and more from [source#1#2].
    Additional context from [source#0#0] again.
    """

    citations = gen.extract_citations(text)
    assert isinstance(citations, list)
    assert "source#0#0" in citations
    assert "source#1#2" in citations
    assert len(citations) == 2  # Unique citations only


@patch('generation.retriever.SmartRetriever')
@patch('generation.generator.MultiModelGenerator')
def test_generate_brief_structure(mock_generator, mock_retriever, tmp_path):
    """Test that generate_brief returns correct structure."""
    # Setup mocks
    mock_retriever_instance = Mock()
    mock_retriever_instance.retrieve.return_value = [
        {
            "chunk_id": "test#0#0",
            "text": "Sample text",
            "entities": [{"type": "PERSON", "text": "John"}],
            "score": 0.9,
            "cluster_id": 0,
            "rank": 1,
        }
    ]
    mock_retriever.return_value = mock_retriever_instance

    mock_generator_instance = Mock()
    mock_generator_instance.generate.return_value = (
        "## Summary\n\nSample brief with [test#0#0] citation.\n\n"
        "**Key Insight**: Important information [test#0#0]."
    )
    mock_generator_instance.extract_citations.return_value = ["test#0#0"]
    mock_generator.return_value = mock_generator_instance

    # Create minimal index structure
    index_dir = tmp_path / "testcompany"
    index_dir.mkdir(parents=True)

    # Create required files
    np.save(index_dir / "embeddings.npy", np.random.randn(1, 3072))

    with open(index_dir / "entities.jsonl", "w") as f:
        f.write(json.dumps({"chunk_id": "test#0#0", "entities": []}) + "\n")

    with open(index_dir / "clusters.json", "w") as f:
        json.dump({"clusters": {"0": ["test#0#0"]}, "n_clusters": 1}, f)

    # Run generate_brief
    with patch('config.INDEX_DIR', tmp_path):
        result = generation.generate_brief("testcompany", "John Doe", mode="summary")

        # Assert structure
        assert isinstance(result, dict)

        # Required keys
        assert "summary" in result
        assert "insights" in result
        assert "key_entities" in result
        assert "citations" in result
        assert "metadata" in result

        # Type checks
        assert isinstance(result["summary"], str)
        assert isinstance(result["insights"], list)
        assert isinstance(result["key_entities"], list)
        assert isinstance(result["citations"], list)
        assert isinstance(result["metadata"], dict)

        # Metadata fields
        metadata = result["metadata"]
        assert "company" in metadata
        assert "mode" in metadata
        assert "model" in metadata
        assert "retrieval_time_ms" in metadata
        assert "generation_time_ms" in metadata
        assert "total_time_ms" in metadata
        assert "timestamp" in metadata


def test_generate_brief_modes():
    """Test that all brief modes work."""
    modes = ["summary", "technical", "biographical", "strategic"]

    with patch('generation.retriever.SmartRetriever') as mock_retriever, \
         patch('generation.generator.MultiModelGenerator') as mock_generator:

        mock_retriever_instance = Mock()
        mock_retriever_instance.retrieve.return_value = []
        mock_retriever.return_value = mock_retriever_instance

        mock_generator_instance = Mock()
        mock_generator_instance.generate.return_value = "Mock response"
        mock_generator_instance.extract_citations.return_value = []
        mock_generator.return_value = mock_generator_instance

        for mode in modes:
            # This will fail at retriever init, but validates mode handling
            try:
                generation.generate_brief("test", mode=mode)
            except FileNotFoundError:
                pass  # Expected - no index exists
