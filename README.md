# RAG Pipeline - Legal Document Retrieval System

A complete end-to-end RAG (Retrieval-Augmented Generation) system for legal document search and question answering. This system extracts text from PDF documents, generates hybrid embeddings, stores them in Pinecone vector database, and provides a Flask REST API for semantic search with LLaMA 3.1 8B.

## System Overview

This repository contains three integrated pipelines that work together:

```
┌─────────────────────┐
│  1. Data Engineering │  PDF → Text Extraction → Parquet
│     (ECS/Fargate)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Pinecone Embedding│  Parquet → Embeddings → Vector DB
│     (Local/Batch)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   3. RAG Query API   │  Query → Retrieval → LLM Response
│      (EC2 GPU)       │
└─────────────────────┘
```

### Pipeline 1: Data Engineering (`data-engineering/`)

Extracts text from legal PDF documents stored in S3 and produces chunked Parquet files.

**Key Features:**
- Layout-aware text extraction with PyMuPDF
- OCR fallback with Tesseract for scanned documents
- Intelligent text chunking with configurable overlap
- Outputs Parquet files partitioned by state/county
- Runs as containerized ECS tasks on AWS

**Deployment:** AWS ECS (Fargate) via ECR

📖 **[Read Full Documentation](data-engineering/README.md)**

---

### Pipeline 2: Pinecone Embedding (`pinecone-embedding/`)

Generates hybrid embeddings (dense + sparse) from Parquet files and indexes them in Pinecone.

**Key Features:**
- Dense embeddings via `llama-text-embed-v2`
- Sparse embeddings via `pinecone-sparse-english-v0`
- Batch processing with retry logic
- Flexible metadata mapping from Parquet columns
- Progress tracking for long-running ingestion

**Deployment:** Local or batch processing (requires `uv`)

📖 **[Read Full Documentation](pinecone-embedding/README.md)**

---

### Pipeline 3: RAG Query API (`rag-query/`)

Production Flask REST API for querying legal documents using vector search and LLM generation.

**Key Features:**
- **REST API:** Flask on port 8000 with JSON responses
- **Two Search Modes:**
  - Baseline: Dense embedding search (faster)
  - Hybrid: Dense + Sparse + Cross-encoder reranking (more accurate)
- **Advanced Filtering:** Location, binary tags, numeric ranges
- **GPU Optimized:** 4-bit quantization, LLaMA 3.1 8B
- **Docker Ready:** One-command deployment with GPU support

**Deployment:** AWS EC2 (GPU instance) via Docker

📖 **[Read Full Documentation](rag-query/README.md)**

---

## Quick Start

### Complete System Setup

1. **Extract PDFs to Parquet (Data Engineering)**
   ```bash
   cd data-engineering
   # Build and push to ECR
   docker build -t data-engineering .
   docker tag data-engineering:latest <account>.dkr.ecr.us-east-1.amazonaws.com/data-engineering:latest
   docker push <account>.dkr.ecr.us-east-1.amazonaws.com/data-engineering:latest

   # Run on ECS (see data-engineering/README.md for task definition)
   ```

2. **Generate Embeddings (Pinecone Embedding)**
   ```bash
   cd pinecone-embedding
   # Install dependencies
   uv sync

   # Set up environment
   cp .env.example .env
   # Add PINECONE_API_KEY to .env

   # Run ingestion
   uv run python src/rag_ingest/ingest.py \
       --index-name "rag-prod-index" \
       --bucket "your-s3-bucket" \
       --prefix "processed/zone=text_chunk/" \
       --metadata-cols county state url
   ```

3. **Deploy Query API (RAG Query)**
   ```bash
   cd rag-query
   # Set up environment
   cp .env.example .env
   # Add PINECONE_API_KEY and HF_TOKEN to .env

   # Build and run with Docker
   ./build.sh && ./run.sh

   # Test the API
   curl http://localhost:8000/health
   ```

---

## Architecture

### Data Flow

```
┌──────────────┐
│  PDF Files   │ (S3: input/pdfs/)
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│  Data Engineering        │
│  - PyMuPDF extraction    │
│  - Tesseract OCR         │
│  - Text chunking         │
└──────┬───────────────────┘
       │
       ▼
┌──────────────┐
│ Parquet Files│ (S3: processed/zone=text_chunk/)
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│  Pinecone Embedding      │
│  - Dense embeddings      │
│  - Sparse embeddings     │
│  - Metadata indexing     │
└──────┬───────────────────┘
       │
       ▼
┌──────────────┐
│  Pinecone DB │ (Vector index with hybrid search)
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│  RAG Query API           │
│  - Vector retrieval      │
│  - Reranking             │
│  - LLM generation        │
└──────┬───────────────────┘
       │
       ▼
┌──────────────┐
│ JSON Response│ (Frontend/Streamlit)
└──────────────┘
```

### Tech Stack

| Component | Technologies |
|-----------|-------------|
| **Data Engineering** | Python 3.11, PyMuPDF, Tesseract OCR, Pandas, AWS ECS/Fargate |
| **Embedding** | Pinecone Inference API, LLaMA embeddings, Sparse embeddings, `uv` |
| **Query API** | Flask, Pinecone, LLaMA 3.1 8B (4-bit), PyTorch, Transformers, Docker |
| **Infrastructure** | AWS S3, ECR, ECS, EC2 (g4dn.xlarge GPU) |

---

## Project Structure

```
rag-pipeline/
│
├── data-engineering/           # Pipeline 1: PDF → Parquet
│   ├── main.py                 # Text extraction script
│   ├── Dockerfile              # ECS container definition
│   ├── requirements.txt        # Python dependencies
│   └── README.md               # Full documentation
│
├── pinecone-embedding/         # Pipeline 2: Parquet → Vector DB
│   ├── src/
│   │   └── rag_ingest/
│   │       ├── ingest.py       # Main ingestion script
│   │       ├── s3_loader.py    # S3 data loading
│   │       ├── embed_dense.py  # Dense embedding generation
│   │       ├── embed_sparse.py # Sparse embedding generation
│   │       └── upsert.py       # Pinecone upsert logic
│   ├── tests/                  # Unit tests
│   ├── pyproject.toml          # uv dependencies
│   └── README.md               # Full documentation
│
├── rag-query/                  # Pipeline 3: Query API
│   ├── api.py                  # Flask REST API (main entry)
│   ├── pipeline.py             # RAG orchestration
│   ├── models.py               # LLM/reranker loading
│   ├── retrieval.py            # Pinecone retrieval
│   ├── llm_generation.py       # LLM response generation
│   ├── filters.py              # Filter processing
│   ├── utils.py                # Utility functions
│   ├── config.py               # Configuration
│   ├── main.py                 # CLI entry point
│   ├── Dockerfile              # Docker image
│   ├── docker-compose.yml      # Docker Compose config
│   ├── .env.example            # Environment template
│   ├── .dockerignore           # Docker ignore rules
│   ├── Documentation/          # Detailed guides
│   │   ├── EC2_SETUP.md        # EC2 deployment guide
│   │   ├── QUICKSTART.md       # 5-minute quick start
│   │   ├── DEPLOYMENT_CHECKLIST.md
│   │   └── PROJECT_SUMMARY.md
│   └── README.md               # Full documentation
│
└── README.md                   # This file
```

---

## Prerequisites

### For Data Engineering
- Docker
- AWS Account (S3, ECR, ECS)
- AWS CLI configured

### For Pinecone Embedding
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Pinecone API Key
- AWS credentials (S3 read access)

### For RAG Query API
- Docker with NVIDIA Container Toolkit
- AWS EC2 GPU instance (g4dn.xlarge or larger)
- Pinecone API Key
- Hugging Face Token

---

## Configuration

### Environment Variables

Each pipeline requires specific environment variables:

**Data Engineering:**
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

**Pinecone Embedding:**
```env
PINECONE_API_KEY=pc_sk_...
```

**RAG Query API:**
```env
PINECONE_API_KEY=pc_sk_...
HF_TOKEN=hf_...
```

---

## API Reference

### Query Endpoint

**POST** `/query`

**Request:**
```json
{
  "query": "What are the dog leash regulations?",
  "filters": {
    "locations": [
      {
        "state": "ca",
        "county": ["alameda-county", "san-francisco-county"]
      }
    ],
    "binary_tags": {
      "penalty": true
    },
    "numeric_ranges": {
      "fk_grade": {"min": 0, "max": 12}
    }
  },
  "mode": "hybrid"
}
```

**Response:**
```json
{
  "response": "According to the legal documents, dogs must be...",
  "chunks": [
    {
      "id": "ca_alameda_doc123_chunk5",
      "score": 0.89,
      "rerank_score": 0.95,
      "chunk_text": "All dogs must be on a leash...",
      "county": "alameda-county",
      "state": "ca",
      "section": "Animal Control"
    }
  ],
  "mode": "hybrid"
}
```

### Health Check

**GET** `/health`

**Response:**
```json
{
  "status": "healthy",
  "gpu": "available"
}
```

---

## Deployment Guides

### Development
- Local testing with Docker Compose
- CLI mode for debugging
- Unit tests for components

### Production
- **Data Engineering:** Deploy to AWS ECS with Fargate
- **Pinecone Embedding:** Run batch jobs locally or on EC2
- **RAG Query API:** Deploy to EC2 GPU instance with Docker

📖 **Detailed deployment guides available in each pipeline's README**

---

## Performance & Costs

### Expected Performance
- **Data Engineering:** ~100 pages/minute (OCR), ~500 pages/minute (text PDFs)
- **Embedding:** ~1000 chunks/minute
- **Query API:** ~2-5 seconds per query (hybrid mode)

### AWS Costs (Estimated Monthly)
- **ECS Task (data-engineering):** ~$50-100/month (depends on usage)
- **S3 Storage:** ~$23/TB/month
- **EC2 g4dn.xlarge (24/7):** ~$380/month
- **Pinecone Serverless:** Varies by usage (see Pinecone pricing)

💡 **Tip:** Stop EC2 instance when not in use to reduce costs

---

## Monitoring & Logging

- **ECS Tasks:** CloudWatch Logs (`/ecs/data-engineering`)
- **Query API:** Docker logs (`docker compose logs -f`)
- **Pinecone:** Built-in progress bars and logging

---

## Troubleshooting

### Common Issues

**Data Engineering:**
- **OCR failures:** Check Tesseract installation and language packs
- **Memory errors:** Increase ECS task memory allocation

**Pinecone Embedding:**
- **Connection timeouts:** Check AWS credentials and S3 bucket permissions
- **Rate limits:** Reduce batch size in `embed_dense.py`

**RAG Query API:**
- **GPU not detected:** Verify NVIDIA Container Toolkit installation
- **Out of memory:** Use larger instance or reduce model size
- **Slow queries:** Enable caching, reduce `HYBRID_TOP_K`

📖 **See individual README files for detailed troubleshooting**

---

## Development

### Running Tests

**Pinecone Embedding:**
```bash
cd pinecone-embedding
uv run python -m unittest discover tests
```

**RAG Query:**
```bash
cd rag-query
python -m pytest tests/  # (if tests exist)
```

### Adding New Features

1. **New metadata fields:** Update Parquet schema in `data-engineering/main.py`
2. **New filters:** Add to `rag-query/filters.py`
3. **New embeddings:** Modify `pinecone-embedding/src/rag_ingest/embed_*.py`

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## License

[Add your license here]

---

## Support

For detailed documentation:
- [Data Engineering Guide](data-engineering/README.md)
- [Pinecone Embedding Guide](pinecone-embedding/README.md)
- [RAG Query API Guide](rag-query/README.md)
- [EC2 Deployment Guide](rag-query/Documentation/EC2_SETUP.md)
- [Quick Start Guide](rag-query/Documentation/QUICKSTART.md)

---

## Acknowledgments

- **Pinecone** for vector database and embedding infrastructure
- **Meta** for LLaMA 3.1 model
- **Hugging Face** for transformers library
- **PyMuPDF** and **Tesseract** for PDF text extraction

---

**Built for semantic search of legal documents with hybrid retrieval and LLM-powered responses.**
