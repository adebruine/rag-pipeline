# Use NVIDIA CUDA base image for GPU support
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    CUDA_HOME=/usr/local/cuda

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install --no-cache-dir --upgrade pip

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py .
COPY models.py .
COPY filters.py .
COPY retrieval.py .
COPY llm_generation.py .
COPY utils.py .
COPY pipeline.py .
COPY main.py .
COPY example_query.json .

# Create outputs directory
RUN mkdir -p outputs

# Set environment variables for the application
# These will be overridden by docker-compose or runtime environment
ENV PINECONE_API_KEY="" \
    HF_TOKEN=""

# Run the application
EXPOSE 8000
CMD ["python3", "api.py"]
