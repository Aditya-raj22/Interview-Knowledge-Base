"""Configuration constants for the Interview KB system."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "interview-kb@example.com")
PUBMED_API_KEY = os.getenv("PUBMED_API_KEY", "")
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")

# Data storage
DATA_DIR = Path(os.getenv("DATA_DIR", "data/raw"))
INDEX_DIR = Path(os.getenv("INDEX_DIR", "data/index"))

# Ingestion settings
MAX_RESULTS_PER_SOURCE = 10  # Limit results from each API
REQUEST_TIMEOUT = 30  # Seconds

# Embedding settings
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072  # text-embedding-3-large dimension
EMBEDDING_BATCH_SIZE = 2048  # Max batch size for OpenAI API
CHUNK_SIZE = 512  # Characters per chunk
CACHE_EMBEDDINGS = True  # Enable caching to save API costs

# Indexing settings
MAX_CHUNKS_PER_DOC = 10
SPACY_MODEL = "en_core_web_sm"  # spaCy model for NER
SPACY_BATCH_SIZE = 128  # Batch size for spaCy processing
CLUSTER_RANGE = (3, 7)  # Min and max clusters for adaptive KMeans

# Generation settings
TOP_K_RESULTS = 5  # Number of relevant chunks to retrieve
MAX_RESPONSE_LENGTH = 500  # Characters
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "gpt-4o")  # gpt-4o or claude-3-5-sonnet-20241022
GENERATION_TEMPERATURE = 0.7
MAX_TOKENS = 2000
ENABLE_STREAMING = False  # Set to True for streaming responses

# Brief generation modes
BRIEF_MODES = ["summary", "technical", "biographical", "strategic"]
