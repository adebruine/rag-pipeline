# RAG Pipeline for Legal Document Retrieval

A modular Retrieval-Augmented Generation (RAG) pipeline for querying legal documents using Pinecone vector database and LLaMA 3.1 8B model.

## Features

- **Two Search Modes:**
  - **Baseline:** Dense embedding search only
  - **Hybrid:** Dense + Sparse embeddings with cross-encoder reranking

- **Filter Support:**
  - Location-based filtering (state, county)
  - Binary tags (penalty, obligation, permission, prohibition)
  - Numeric ranges (Flesch-Kincaid grade, readability, word count, complexity)

- **GPU Optimized:**
  - 4-bit quantization for efficient GPU memory usage
  - Optimized for EC2 GPU instances

- **Docker Ready:**
  - Containerized for easy deployment
  - Supports NVIDIA GPU runtime
  - Simple one-command deployment

- **CSV Export:**
  - Top-K retrieved chunks with metadata
  - LLM-generated summaries and responses

## Project Structure

```
.
├── config.py              # Configuration and environment variables
├── models.py              # Model loading (LLM and reranker)
├── filters.py             # Filter processing utilities
├── retrieval.py           # Pinecone retrieval functions
├── llm_generation.py      # LLM response generation
├── utils.py               # Utility functions (CSV, printing)
├── pipeline.py            # Main RAG pipeline orchestration
├── main.py                # Entry point for execution
├── requirements.txt       # Python dependencies
├── .env.example           # Example environment variables
├── .gitignore             # Git ignore file
├── README.md              # This file
├── example_query.json     # Example query file
│
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose configuration
├── .dockerignore          # Docker ignore file
├── build.sh               # Docker build script
├── run.sh                 # Docker run script
└── EC2_SETUP.md           # EC2 deployment guide
```

## Setup

### Deployment Options

You can deploy this pipeline in two ways:

1. **Docker (Recommended for EC2)** - Containerized deployment with GPU support
2. **Direct Python** - Run directly on the host machine

Choose Docker for easy, consistent deployment on EC2 or any containerized environment.

---

## 🐳 Docker Deployment (Recommended)

### Quick Start

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd <repo-directory>

# 2. Set up environment variables
cp .env.example .env
# Edit .env and add your PINECONE_API_KEY and HF_TOKEN

# 3. Build the Docker image
./build.sh

# 4. Run the container
./run.sh
```

### Prerequisites for Docker

- Docker Engine 20.10+
- Docker Compose v2.0+
- NVIDIA Container Toolkit (for GPU support)
- NVIDIA GPU with CUDA support

### EC2 Deployment

For detailed EC2 deployment instructions, see **[EC2_SETUP.md](EC2_SETUP.md)**

#### Quick EC2 Setup:

```bash
# On EC2 instance (Ubuntu 22.04 with GPU)

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Install Docker Compose
sudo apt-get install -y docker-compose-plugin

# Clone and run
git clone <your-repo>
cd <repo-directory>
cp .env.example .env
nano .env  # Add your API keys
./build.sh
./run.sh
```

### Docker Commands

```bash
# Build image
docker build -t rag-pipeline:latest .

# Run with docker-compose
docker compose up          # Foreground
docker compose up -d       # Background
docker compose down        # Stop

# Run with docker directly
docker run --gpus all \
  --env-file .env \
  -v $(pwd)/outputs:/app/outputs \
  rag-pipeline:latest

# Run custom query
docker run --gpus all \
  --env-file .env \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/queries:/app/queries:ro \
  rag-pipeline:latest \
  python3 main.py --mode hybrid --json queries/my_query.json

# Interactive mode
docker run --gpus all --env-file .env -it rag-pipeline:latest /bin/bash

# View logs
docker compose logs -f

# Check GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## 🐍 Direct Python Installation

### 1. Environment Setup

**On EC2 with GPU:**

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.10+ if needed
sudo apt-get install python3.10 python3-pip -y

# Install CUDA (if not already installed)
# Follow NVIDIA's official CUDA installation guide for your Ubuntu version
```

### 2. Clone Repository

```bash
git clone <your-repo-url>
cd <repo-directory>
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

Add your credentials:
```
PINECONE_API_KEY=your_actual_pinecone_api_key
HF_TOKEN=your_actual_huggingface_token
```

**Load environment variables:**
```bash
export $(cat .env | xargs)
```

Or use python-dotenv:
```bash
pip install python-dotenv
```

And modify `config.py` to load from .env:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Usage

### Basic Usage

**Run with example query (from notebook):**
```bash
python main.py --example
```

**Run baseline search (dense embedding only):**
```bash
python main.py --mode baseline --example
```

**Run hybrid search (dense + sparse + reranking):**
```bash
python main.py --mode hybrid --example
```

### Custom Query

**Provide query via command line:**
```bash
python main.py --mode hybrid --query "Are dogs allowed in public parks?"
```

### Using JSON Input

Create a JSON file with your query and filters:

```json
{
  "query": "which counties have laws about dogs?",
  "filters": {
    "locations": [
      {
        "state": "ca",
        "county": ["alameda-county", "butte-county"]
      },
      {
        "state": "ga",
        "county": ["fulton-county"]
      }
    ],
    "penalty": "Y",
    "fk_grade": {"min": 5.0, "max": 50.0}
  }
}
```

Run with JSON:
```bash
python main.py --mode hybrid --json query.json
```

### Filter-Only Search

Leave query empty to search by filters only:

```json
{
  "query": "",
  "filters": {
    "locations": [
      {
        "state": "ca",
        "county": ["alameda-county"]
      }
    ],
    "penalty": "Y"
  }
}
```

## Output

The pipeline generates:

1. **Console Output:**
   - Retrieved chunks preview
   - LLM-generated response
   - Processing logs

2. **CSV File** (in `outputs/` directory):
   - `baseline_retrieval_output.csv` - Baseline search results
   - `hybrid_retrieval_output.csv` - Hybrid search results with rerank scores
   - `baseline_filter_only_output.csv` - Filter-only baseline results
   - `hybrid_filter_only_output.csv` - Filter-only hybrid results

**CSV Columns:**
- `id` - Document ID
- `score` - Similarity score
- `rerank_score` - Reranker score (hybrid mode only)
- `state`, `county`, `section` - Location metadata
- `chunk_text` - Full text of the chunk
- `penalty`, `obligation`, `permission`, `prohibition` - Binary tags
- `fk_grade`, `fre`, `wc`, `pct_complex` - Readability metrics

## Configuration

Edit `config.py` to customize:

- Model IDs
- Top-K retrieval settings
- Quantization parameters
- Output paths
- Generation parameters

## GPU Requirements

**Recommended EC2 Instance:**
- `g4dn.xlarge` or larger (NVIDIA T4 GPU, 16GB GPU memory)
- `p3.2xlarge` (NVIDIA V100, 16GB GPU memory)

**Minimum GPU Memory:** 12GB (with 4-bit quantization)

## API Integration

To integrate with a Streamlit frontend:

```python
from pipeline import RAGPipeline

# Initialize once
pipeline = RAGPipeline(use_reranking=True)

# Use in API endpoint
def query_rag(query: str, filters: dict):
    llm_output, csv_filename = pipeline.run(query, filters)
    return {
        "response": llm_output,
        "csv_path": csv_filename
    }
```

## Troubleshooting

**Out of Memory Error:**
- Reduce `HYBRID_TOP_K` in `config.py`
- Use smaller EC2 instance with more GPU memory
- Ensure 4-bit quantization is enabled

**Slow Performance:**
- Ensure GPU is being used: `torch.cuda.is_available()` should return `True`
- Check CUDA installation
- Use `nvidia-smi` to monitor GPU usage

**Model Download Issues:**
- Verify HF_TOKEN is valid and has access to LLaMA models
- Check internet connection on EC2
- Ensure sufficient disk space for model downloads (~16GB)

## License

This project is for use with the UnBarred 2.0 legal database.

## Support

For issues or questions, please contact your development team.
