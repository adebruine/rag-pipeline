from typing import List, Dict, Any, Tuple
import polars as pl
from tqdm import tqdm



def build_vectors_from_df(
    df: pl.DataFrame, 
    dense_embeddings: List[List[float]],
    sparse_embeddings: List[Dict[str, List[float]]],
    metadata: List[str],
    id_template: str = "{county}#chunk{idx}",
) -> Tuple[List[Dict[str, Any]], List[str]]:

    """Build Pinecone vectors objects and corresponding IDs from Polars DataFrame.

    Args:
        df: Polars DataFrame containing text data (rows accessed with .iter_rows(named=True))
        dense_embeddings: dense embeddings vectors (length matches number of rows in df)
        sparse_embeddings: sparse embedding vectors (length matches number of rows in df)
        metadata: List columns to include in metadata
        id_template: a python format string for generating unique vector IDs

    Returns:
        Tuple of (vectors, ids) where:
            - vectors: List[dict] each with keys "id","values","sparse_values","metadata"
            - ids: List[str] alignment list of ids (same order as vectors)
    """

    if not (len(df) == len(dense_embeddings) == len(sparse_embeddings)):
        raise ValueError("df, dense_embeddings, and sparse_embeddings must have the same length")



    vectors: List[Dict[str, Any]] = []
    ids: List[str] = []

    for idx, row in enumerate(df.iter_rows(named=True)):
        try:
            id_str = id_template.format(**row, idx=idx)
        except Exception:
            id_str = f"chunk{idx}"

        # Simplified metadata extraction
        meta = {col: str(row.get(col, "")) for col in metadata}
        
        vectors.append({
            "id": id_str,
            "values": dense_embeddings[idx],
            "sparse_values": sparse_embeddings[idx],
            "metadata": meta
        })
        ids.append(id_str)

    return vectors, ids


def upsert(
    index,
    ids: List[str],
    dense_vectors: List[List[float]],
    sparse_vectors: List[Dict[str, List[float]]],
    metadata: List[Dict[str, Any]],
    batch_size: int = 100
) -> Dict[str, Any]:
    """Upsert dense & sparse vectors into Pinecone index in batches."""

    total = len(ids)

    # Good validation here
    if not len(dense_vectors) == total == len(sparse_vectors) == len(metadata):
        raise ValueError("dense_vectors, sparse_vectors, and metadata must have the same length as ids")

    for i in tqdm(range(0, total, batch_size), desc="Upserting to Pinecone"):

        
        batch_ids = ids[i:i + batch_size]
        
        # Slicing logic for the other lists to match batch_ids
        batch_dense = dense_vectors[i:i + batch_size]
        batch_sparse = sparse_vectors[i:i + batch_size]
        batch_meta = metadata[i:i + batch_size]

        batch = []
        for j, vec_id in enumerate(batch_ids):
            batch.append({
                "id": vec_id,
                "values": batch_dense[j],
                "sparse_values": batch_sparse[j],
                "metadata": batch_meta[j],
            })

        if batch:
            index.upsert(vectors=batch)

    return index.describe_index_stats()
