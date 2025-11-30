from typing import List, Dict
import polars as pl
from tqdm import tqdm

def embed_sparse(
    pc,
    df: pl.DataFrame,
    text_col: str = "chunk_text",
    embed_model = "pinecone-sparse-english-v0",
    batch_size = 96
) -> List[Dict[str,List[float]]]:

    """Generate sparse embeddings for text using Pinecone Inference API.

    Args:
        pc: Pinecone index object
        df: Polars DataFrame containing text data
        text_col: Name of the column containing text data
        embed_model: Name of the Pinecone embed model to use
        batch_size: Batch size for embedding

    Returns:
        List of Dicts of floats representing the embeddings
    """


    all_chunks = df[text_col].to_list()
    sparse_embeddings:List[Dict[str, List[float]]] = []

    for i in tqdm(range(0, len(all_chunks), batch_size), desc="Sparse Embedding"):
        chunk_batch = all_chunks[i:i + batch_size]

        try:
            result = pc.inference.embed(
                model=embed_model,
                inputs = chunk_batch,
                parameters={"input_type": "passage", "truncate": "END"},
            )
        
        except Exception:
            result = pc.inference.embed(
                model=embed_model,
                inputs=chunk_batch,
                parameters={"input_type": "passage", "truncate":"END"}
            )

        sparse_embeddings.extend([
            {
                "indices": item.get("sparse_indices",[]),
                "values": item.get("sparse_values",[]),
            }
            for item in result
        ])

    return sparse_embeddings