import time
from typing import List, Dict
import polars as pl
from tqdm import tqdm
from pinecone.exceptions.exceptions import PineconeApiException

def embed_sparse(
    pc,
    df: pl.DataFrame,
    text_col: str = "chunk_text",
    embed_model = "pinecone-sparse-english-v0",
    batch_size = 96,
    requests_per_minute: int = 5
) -> List[Dict[str,List[float]]]:

    """Generate sparse embeddings for text using Pinecone Inference API.

    Args:
        pc: Pinecone index object
        df: Polars DataFrame containing text data
        text_col: Name of the column containing text data
        embed_model: Name of the Pinecone embed model to use
        batch_size: Batch size for embedding
        requests_per_minute: Max requests per minute to stay under rate limit

    Returns:
        List of Dicts of floats representing the embeddings
    """

    all_chunks = df[text_col].to_list()
    sparse_embeddings:List[Dict[str, List[float]]] = []
    delay_between_requests = 60.0 / requests_per_minute

    for i in tqdm(range(0, len(all_chunks), batch_size), desc="Sparse Embedding"):
        chunk_batch = all_chunks[i:i + batch_size]

        max_retries = 5
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                result = pc.inference.embed(
                    model=embed_model,
                    inputs=chunk_batch,
                    parameters={"input_type": "passage", "truncate": "END"},
                )
                break
            except PineconeApiException as e:
                if e.status == 429 and attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise

        for item in result:
            sparse_embedding = {
                "indices": item.sparse_indices,
                "values": item.sparse_values,
            }
            print(f"DEBUG: Generated embedding - indices: {len(sparse_embedding['indices'])}, values: {len(sparse_embedding['values'])}")
            if len(sparse_embedding['indices']) == 0:
                print(f"WARNING: Empty sparse embedding generated! Using placeholder.")
                # Use a placeholder sparse embedding instead of skipping
                sparse_embedding = {
                    "indices": [0],  # Single index
                    "values": [0.001],  # Very small value
                }
            sparse_embeddings.append(sparse_embedding)


        # Rate limiting: wait between batches
        time.sleep(delay_between_requests)

    return sparse_embeddings
