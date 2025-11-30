import argparse
import os

import polars as pl

from rag_ingest.pinecone_setup import init_pinecone
from rag_ingest.s3_loader import load_parquet_from_s3
from rag_ingest.embed_dense import embed_dense
from rag_ingest.embed_sparse import embed_sparse
from rag_ingest.upsert import build_vectors_from_df, upsert


def parse_args():
    parser = argparse.ArgumentParser(description="RAG Ingestion Pipeline")

    parser.add_argument(
        "--index-name",
        required=True,
        help="Name of the Pinecone index to write to",
    )

    parser.add_argument(
        "--bucket",
        required=True,
        help="S3 bucket where parquet files live",
    )

    parser.add_argument(
        "--prefix",
        required=False,
        default=None,
        help="S3 prefix containing parquet shards",
    )

    parser.add_argument(
        "--single-key",
        required=False,
        default=None,
        help="Single parquet file key to load instead of directory",
    )

    parser.add_argument(
        "--metadata-cols",
        nargs="*",       # Allow 0 or more arguments
        required=False,  # Not required
        default=[],      # Default to empty list
        help="Column names to attach as metadata to each vector. If omitted, all columns are used.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Initialize Pinecone index
    pc, index = init_pinecone(
        index_name=args.index_name,
        dimension=1024,
        region="us-east-1",
    )

    # Load parquet(s) from S3
    df = load_parquet_from_s3(
        bucket=args.bucket,
        prefix=args.prefix,
        single_key=args.single_key,
        region="us-east-1",
    )

    # Logic to determine metadata columns
    if not args.metadata_cols:
        # Use ALL columns (including chunk_text) if none provided
        meta_cols = df.columns
    else:
        meta_cols = args.metadata_cols

    # Generate dense embeddings
    dense_vecs = embed_dense(
        pc=pc,
        df=df,
        text_col="chunk_text",
        embed_model="llama-text-embed-v2",
        batch_size=96,
    )

    # Generate sparse embeddings
    sparse_vecs = embed_sparse(
        pc=pc,
        df=df,
        text_col="chunk_text",
        embed_model="pinecone-sparse-english-v0",
        batch_size=96,
    )

    # Build metadata + vector objects
    vectors, ids = build_vectors_from_df(
        df=df,
        dense_embeddings=dense_vecs,
        sparse_embeddings=sparse_vecs,
        metadata=meta_cols,  # Use the variable 'meta_cols' here, NOT args.metadata_cols
        id_template="{county}#chunk{idx}",  # customize later if needed
    )

    # Extract metadata list in the same order
    metadata_list = [v["metadata"] for v in vectors]

    #  Upsert into Pinecone
    stats = upsert(
        index=index,
        ids=ids,
        dense_vectors=dense_vecs,
        sparse_vectors=sparse_vecs,
        metadata=metadata_list,
        batch_size=100,
    )

    print("\nIngestion Complete!")
    print(stats)


if __name__ == "__main__":
    main()
