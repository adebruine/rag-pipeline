"""
Model loading and initialization for RAG pipeline.
"""
from sentence_transformers.cross_encoder import CrossEncoder

from config import Config


def initialize_reranker() -> CrossEncoder:
    """
    Initialize and load the reranker model.

    Returns:
        CrossEncoder model for reranking
    """
    print(f"Loading reranker model: {Config.RERANKER_MODEL_ID}")
    reranker_model = CrossEncoder(Config.RERANKER_MODEL_ID)
    print("Reranker model loaded successfully.")
    return reranker_model