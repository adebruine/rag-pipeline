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
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    
    # Pinecone Configuration
    PINECONE_INDEX_NAME: str = "hybrid-search-index"
    PINECONE_NAMESPACE: str = "__default__"
    VECTOR_DIMENSION: int = 1024
    
    # Model Configuration
    LLM_MODEL_ID: str = "meta-llama/Llama-3.1-8B-Instruct"
    EMBEDDING_MODEL_DENSE: str = "llama-text-embed-v2"
    EMBEDDING_MODEL_SPARSE: str = "pinecone-sparse-english-v0"
    RERANKER_MODEL_ID: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Quantization Settings
    LOAD_IN_4BIT: bool = True
    BNB_4BIT_USE_DOUBLE_QUANT: bool = True
    BNB_4BIT_QUANT_TYPE: str = "nf4"
    
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
    BASELINE_CSV_FILENAME: str = "baseline_retrieval_output.csv"
    BASELINE_FILTER_CSV_FILENAME: str = "baseline_filter_only_output.csv"
    HYBRID_CSV_FILENAME: str = "hybrid_retrieval_output.csv"
    HYBRID_FILTER_CSV_FILENAME: str = "hybrid_filter_only_output.csv"
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is set."""
        if not cls.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY environment variable is not set")
        if not cls.HF_TOKEN:
            raise ValueError("HF_TOKEN environment variable is not set")
    
    @classmethod
    def get_output_path(cls, filename: str) -> str:
        """Get full output path for a file."""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        return os.path.join(cls.OUTPUT_DIR, filename)
