#!/bin/bash

# Run script for RAG Pipeline Docker container

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Please create a .env file with your API keys:"
    echo "  cp .env.example .env"
    echo "  # Edit .env and add your PINECONE_API_KEY and HF_TOKEN"
    exit 1
fi

echo "Starting RAG Pipeline container..."
echo ""

# Run with docker-compose (recommended)
docker-compose up

# Alternative: Run directly with docker
# docker run --gpus all \
#   --env-file .env \
#   -v $(pwd)/outputs:/app/outputs \
#   -v $(pwd)/queries:/app/queries:ro \
#   --name rag-pipeline \
#   --rm \
#   rag-pipeline:latest
