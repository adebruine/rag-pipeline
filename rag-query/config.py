"""
Configuration file for RAG pipeline.
Environment variables and model configurations.
"""
import os
from typing import Optional

class Config:
    """Configuration class for RAG pipeline."""
    
    # API Keys - Load from environment variables
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Pinecone Configuration
    PINECONE_INDEX_NAME: str = "test-index"
    PINECONE_NAMESPACE: str = "__default__"
    VECTOR_DIMENSION: int = 1024

    # Model Configuration
    CLAUDE_MODEL: str = "claude-haiku-4-5-20251001"
    EMBEDDING_MODEL_DENSE: str = "multilingual-e5-large"
    EMBEDDING_MODEL_SPARSE: str = "pinecone-sparse-english-v0"
    RERANKER_MODEL_ID: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Retrieval Configuration
    BASELINE_TOP_K: int = 5
    HYBRID_TOP_K: int = 100
    FILTER_ONLY_TOP_K: int = 1000
    RERANK_TOP_N: int = 5
    
    # LLM Generation Settings
    MAX_NEW_TOKENS: int = 1024
    DO_SAMPLE: bool = False
    
    # Output Configuration
    OUTPUT_DIR: str = "outputs"
    # BASELINE_CSV_FILENAME: str = "baseline_retrieval_output.csv"
    # BASELINE_FILTER_CSV_FILENAME: str = "baseline_filter_only_output.csv"
    # HYBRID_CSV_FILENAME: str = "hybrid_retrieval_output.csv"
    # HYBRID_FILTER_CSV_FILENAME: str = "hybrid_filter_only_output.csv"
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is set."""
        if not cls.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY environment variable is not set")
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    
    @classmethod
    def get_output_path(cls, filename: str) -> str:
        """Get full output path for a file."""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        return os.path.join(cls.OUTPUT_DIR, filename)
