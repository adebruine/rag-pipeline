#!/bin/bash

# Build script for RAG Pipeline Docker image

echo "Building RAG Pipeline Docker image..."

# Build the Docker image
docker build -t rag-pipeline:latest .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo ""
    echo "To run the container:"
    echo "  docker-compose up"
    echo ""
    echo "Or run directly:"
    echo "  docker run --gpus all --env-file .env -v \$(pwd)/outputs:/app/outputs rag-pipeline:latest"
else
    echo "❌ Docker build failed!"
    exit 1
fi
