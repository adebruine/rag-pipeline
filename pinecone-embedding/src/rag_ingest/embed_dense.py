from typing import List
import polars as pl
from tqdm import tqdm

def embed_dense(
    pc,
    df: pl.DataFrame,
    text_col:str = "chunk_text",
    embed_model: str = "llama-text-embed-v2",
    batch_size: int = 96
) -> List[List[float]]:

    """Embed dense text data using Pinecone.

    Args:
        pc: Pinecone client instance
        df: Polars DataFrame containing text data
        text_col: Name of the column containing text data
        embed_model: Name of the Pinecone embed model to use
        batch_size: Batch size for embedding

    Returns:
        List of lists of floats representing the embeddings
    """

    all_chunks = df[text_col].to_list()
    dense_embeddings = []

    # WRAP range() with tqdm
    # total=len(all_chunks) allows tqdm to estimate time remaining
    # step=batch_size ensures the bar updates correctly
    for i in tqdm(range(0, len(all_chunks), batch_size), desc="Dense Embedding"):
        chunk_batch = all_chunks[i:i+batch_size]

        try:
            result = pc.inference.embed(
                model=embed_model,
                inputs=chunk_batch,
                parameters={"input_type": "passage", "truncate": "END"},
            )
            dense_embeddings.extend([x["values"] for x in result])

        except Exception:
            # single retry batch
            result = pc.inference.embed(
                model=embed_model,
                inputs=chunk_batch,
                parameters={"input_type": "passage", "truncate": "END"},
            )
            dense_embeddings.extend([x["values"] for x in result])
    return dense_embeddings