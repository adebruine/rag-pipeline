# Data Engineering Pipeline

A containerized PDF text extraction pipeline that runs on AWS ECS. This service reads PDF files from S3, extracts text 
using layout-aware parsing and optical character recognition (OCR), chunks the content, and outputs Parquet files partitioned by state and county.

**Location**: `rag-pipeline/data-engineering/`

## Overview

This pipeline is **Step 1** in the RAG system:

1. **This pipeline** (`data-engineering/`): Extracts text from PDFs in S3 ’ Chunks content ’ Outputs Parquet files
2. **Pinecone Embedding** (`pinecone-embedding/`): Reads Parquet files ’ Generates embeddings ’ Stores in Pinecone
3. **RAG Query API** (`rag-query/`): Queries Pinecone ’ Retrieves chunks ’ Generates responses

## Features

- **Dual Extraction Modes**: Layout-aware text extraction via PyMuPDF with OCR fallback using Tesseract
- **Intelligent Chunking**: Semantic chunking with configurable chunk size and overlap
- **S3 Integration**: Direct read from S3 buckets, write to S3 with partitioned output
- **Parquet Output**: Efficient columnar storage with state/county partitioning
- **ECS Deployment**: Runs as containerized tasks on AWS Elastic Container Service
- **Robust Processing**: Handles scanned PDFs, malformed documents, and large files

## Prerequisites

- Docker (for local testing)
- AWS Account with:
  - S3 bucket for input PDFs and output Parquet files
  - ECR repository for Docker images
  - ECS cluster for running tasks
  - IAM role with appropriate permissions (see below)
- AWS CLI configured locally

## Local Development

### Installation

0. **Start virtual environment**
    ```bash
    cd rag-pipeline
    source .venv/bin/activate
    ```
1. **Navigate to the directory:**
   ```bash
   cd data-engineering
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
    NOTE: Audrey ran into some package version issues that she resolved manually, and may have also needed to run `brew install tesselate`


3. **Set up AWS credentials:**

   (Skip this step for local development.)

    Ensure your AWS credentials are configured via `~/.aws/credentials` or environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

### Local Testing

Run the extraction pipeline locally:

```bash
python main.py \
    --input input/pdfs/ \
    --output processed/zone=text_chunk/ \
    --state california \
    --county alameda
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
 | `--input` | Yes | local `file/folder` OR `s3://bucket/prefix` OR `s3://bucket/file.pdf`
| `--output` | Yes | S3 prefix for output Parquet files (`s3://bucket/env=prod[/]` (recommended) OR a local dir (for local runs)) |
 | `--env/--zone/--state/--county` | No | optional metadata (still written into parquet)
| `--chunk-size` | No | Maximum chunk size in characters (default: 1000) |
| `--chunk-overlap` | No | Overlap between chunks in characters (default: 200) |
| `--no-ocr` | No | disable OCR fallback 
| `--s3-max` | No | limit number of PDFs processed from S3 (0 = no limit)

## AWS Deployment

### Step 1: Build and Push Docker Image to ECR

1. **Authenticate Docker to ECR:**
   ```bash
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   ```

2. **Build the Docker image:**
   ```bash
   cd rag-pipeline/data-engineering
   docker build -t data-engineering .
   ```

3. **Tag the image:**
   ```bash
   docker tag data-engineering:latest \
     <account-id>.dkr.ecr.us-east-1.amazonaws.com/data-engineering:latest
   ```

4. **Push to ECR:**
   ```bash
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/data-engineering:latest
   ```

### Step 2: Create ECS Task Definition

Create a task definition JSON file (`task-definition.json`):

```json
{
  "family": "data-engineering-pdf-extraction",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<account-id>:role/dataEngineeringTaskRole",
  "containerDefinitions": [
    {
      "name": "pdf-extractor",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/data-engineering:latest",
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/data-engineering",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "command": [
        "--bucket", "your-s3-bucket",
        "--input-prefix", "input/pdfs/ca/alameda/",
        "--output-prefix", "processed/zone=text_chunk/",
        "--state", "california",
        "--county", "alameda"
      ]
    }
  ]
}
```

Register the task definition:
```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Step 3: Run ECS Task

```bash
aws ecs run-task \
  --cluster your-ecs-cluster \
  --launch-type FARGATE \
  --task-definition data-engineering-pdf-extraction \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx]}"
```

## IAM Permissions

### Task Execution Role
The ECS task execution role needs permissions to pull images from ECR and write logs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

### Task Role
The ECS task role needs S3 read/write permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket/input/*",
        "arn:aws:s3:::your-bucket"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket/processed/*"
      ]
    }
  ]
}
```

## Output Format

The pipeline outputs Parquet files with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Unique chunk identifier (format: `{state}_{county}_{filename}_{chunk_index}`) |
| `text` | string | Extracted chunk text content |
| `state` | string | State name (e.g., `california`) |
| `county` | string | County name (e.g., `alameda`) |
| `source_file` | string | Original PDF filename |
| `page_number` | int | Page number in source PDF |
| `chunk_index` | int | Sequential chunk number within document |

### Partitioning

Output files are partitioned by state and county:
```
s3://your-bucket/processed/zone=text_chunk/state=california/county=alameda/chunks_001.parquet
```

## Project Structure

```
data-engineering/
    main.py              # Main entry point and orchestration
    Dockerfile           # Container definition with Tesseract OCR
    requirements.txt     # Python dependencies
    README.md            # This file
```

## How It Works

1. **List PDFs**: Scans S3 input prefix for all `.pdf` files
2. **Download**: Streams PDF from S3 to memory
3. **Extract Text**:
   - Attempts layout-aware extraction with PyMuPDF
   - Falls back to Tesseract OCR for scanned/image-based PDFs
4. **Chunk**: Splits text into overlapping chunks (default: 1000 chars, 200 overlap)
5. **Format**: Creates DataFrame with metadata (state, county, page, source file)
6. **Upload**: Writes Parquet file to S3 with partitioned path

## Monitoring

View logs in CloudWatch:
```bash
aws logs tail /ecs/data-engineering --follow
```

## Next Steps

After this pipeline completes:

1. **Verify output**: Check S3 for Parquet files in `processed/zone=text_chunk/`
2. **Run embedding pipeline**: Use `pinecone-embedding/` to generate embeddings from Parquet files
3. **Deploy query API**: Use `rag-query/` to enable search and retrieval

See:
- [`../pinecone-embedding/README.md`](../pinecone-embedding/README.md) for the embedding pipeline
- [`../rag-query/README.md`](../rag-query/README.md) for the query API
