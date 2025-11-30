# Pinecone Embedding Pipeline

A robust data ingestion pipeline for embedding and indexing pre-chunked legal documents into Pinecone. This tool loads pre-chunked text data from AWS S3 (Parquet format), generates hybrid embeddings (Dense + Sparse) using Pinecone Inference, and upserts the vectors into a Pinecone serverless index.

**Location**: `rag-pipeline/pinecone-embedding/`

## Features

- **Hybrid Search Support**: Generates both Dense (via `llama-text-embed-v2`) and Sparse (via `pinecone-sparse-english-v0`) embeddings.
- **S3 Integration**: Loads Parquet files directly from S3 (supports single file or directory prefix).
- **Scalable**: Uses batching and retry logic for reliable ingestion.
- **Metadata Handling**: flexible metadata mapping from Parquet columns to Pinecone vector metadata.
- **Progress Tracking**: Built-in progress bars for long-running operations.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (for dependency management)
- AWS Credentials (with read access to the S3 bucket)
- Pinecone API Key

## Installation

1. **Navigate to the directory:**
   ```bash
   cd rag-pipeline/pinecone-embedding
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```
   or
   ```bash
   uv pip install -e .
   ```

3. **Set up Environment Variables:**
   Create a `.env` file in the `pinecone-embedding` directory:
   ```bash
   touch .env
   ```
   Add your Pinecone API Key:
   ```env
   PINECONE_API_KEY=pc_sk_...
   ```

   *Note: AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) are read automatically from your environment or `~/.aws/credentials` via `boto3`.*

## Usage

Run the ingestion script using `uv run`.

### Basic Command

```bash
uv run python src/rag_ingest/ingest.py \
    --index-name "my-index-name" \
    --bucket "my-s3-bucket" \
    --single-key "path/to/file.parquet" \
    --metadata-cols county state url
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--index-name` | Yes | Name of the Pinecone index. It will be created if it doesn't exist. |
| `--bucket` | Yes | S3 Bucket name containing the source data. |
| `--prefix` | No | S3 prefix (folder) to ingest all `.parquet` files from. |
| `--single-key` | No | Specific S3 key to ingest a single file. (Mutually exclusive with `--prefix` recommended). |
| `--metadata-cols` | No | List of columns to attach as metadata. If omitted, **all columns**  are used. |

### Examples

**Ingest a single file with specific metadata:**
```bash
uv run python src/rag_ingest/ingest.py \
    --index-name "rag-prod-index" \
    --bucket "rag-data-lake" \
    --single-key "processed/ca_alameda_chunks.parquet" \
    --metadata-cols county state doc_id page section
```

**Ingest an entire folder (prefix) using standard AWS profile:**
```bash
export AWS_PROFILE=my-profile
uv run python src/rag_ingest/ingest.py \
    --index-name "rag-prod-index" \
    --bucket "rag-data-lake" \
    --prefix "processed/zone=text_chunk/"
```

## Development & Testing

The project uses `unittest` for testing.

**Run all tests:**
```bash
uv run python -m unittest discover tests
```

**Run a specific test file:**
```bash
uv run python -m unittest tests/test_ingest.py
```

### Project Structure

```
pinecone-embedding/
├── src/
│   └── rag_ingest/
│       ├── ingest.py          # Main entry point
│       ├── s3_loader.py       # S3 loading logic
│       ├── pinecone_setup.py  # Index creation/connection
│       ├── embed_dense.py     # Dense embedding logic
│       ├── embed_sparse.py    # Sparse embedding logic
│       └── upsert.py          # Vector construction & upload
├── tests/                     # Unit and Integration tests
├── pyproject.toml             # Dependencies
├── .env                       # Environment variables (create this)
└── README.md                  # This file
```

## Relationship to RAG Query

This pipeline **prepares the data** that the RAG Query API (in `rag-query/`) searches against:

1. **This pipeline** (`pinecone-embedding/`): Ingests legal documents → Generates embeddings → Stores in Pinecone
2. **RAG Query API** (`rag-query/`): Queries Pinecone → Retrieves relevant chunks → Generates responses with LLaMA

See [`rag-query/README.md`](../rag-query/README.md) for the query/retrieval system.

