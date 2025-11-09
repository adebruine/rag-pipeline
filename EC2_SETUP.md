# EC2 Deployment Guide for RAG Pipeline Docker Container

This guide will help you deploy the RAG pipeline as a Docker container on AWS EC2 with GPU support.

## Prerequisites

- AWS Account with EC2 access
- SSH key pair for EC2 access
- Pinecone API key
- Hugging Face token (with access to LLaMA models)

## Step 1: Launch EC2 Instance

### Recommended Instance Types:

| Instance Type | GPU | GPU Memory | vCPUs | RAM | Hourly Cost* |
|--------------|-----|------------|-------|-----|--------------|
| g4dn.xlarge | T4 | 16 GB | 4 | 16 GB | ~$0.526 |
| g4dn.2xlarge | T4 | 16 GB | 8 | 32 GB | ~$0.752 |
| g5.xlarge | A10G | 24 GB | 4 | 16 GB | ~$1.006 |
| p3.2xlarge | V100 | 16 GB | 8 | 61 GB | ~$3.06 |

*Prices vary by region and are subject to change

### Launch Configuration:

1. **AMI**: Deep Learning AMI GPU PyTorch (Ubuntu 22.04)
   - Or use: Ubuntu Server 22.04 LTS with NVIDIA drivers
2. **Instance Type**: g4dn.xlarge (minimum recommended)
3. **Storage**: 100 GB GP3 (for model downloads)
4. **Security Group**: 
   - SSH (22) from your IP
   - Custom ports if exposing API (optional)

## Step 2: Connect to EC2

```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

## Step 3: Install Docker and NVIDIA Container Toolkit

### Install Docker

```bash
# Update package list
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Log out and back in, or run:
newgrp docker

# Verify Docker installation
docker --version
```

### Install NVIDIA Container Toolkit

```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install NVIDIA Docker runtime
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Install Docker Compose

```bash
# Install Docker Compose
sudo apt-get install -y docker-compose-plugin

# Verify installation
docker compose version
```

## Step 4: Clone Your Repository

```bash
# Clone from GitHub
git clone https://github.com/your-username/your-repo.git
cd your-repo

# Or upload files directly
# scp -i your-key.pem -r ./rag-pipeline ubuntu@<EC2_IP>:~/
```

## Step 5: Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit with your API keys
nano .env
```

Add your credentials:
```bash
PINECONE_API_KEY=your_actual_pinecone_api_key
HF_TOKEN=your_actual_huggingface_token
```

Save and exit (Ctrl+X, then Y, then Enter)

## Step 6: Build Docker Image

```bash
# Build the image
./build.sh

# Or manually:
docker build -t rag-pipeline:latest .
```

**Note**: First build will take 10-15 minutes as it downloads all dependencies.

## Step 7: Run the Container

### Option A: Using Docker Compose (Recommended)

```bash
# Run in foreground (see logs)
docker compose up

# Run in background
docker compose up -d

# View logs
docker compose logs -f

# Stop container
docker compose down
```

### Option B: Using Docker Run

```bash
docker run --gpus all \
  --env-file .env \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/queries:/app/queries:ro \
  --name rag-pipeline \
  --rm \
  rag-pipeline:latest
```

## Step 8: Run Custom Queries

### Using JSON Files

1. Create a query file in the `queries/` directory:

```bash
mkdir -p queries
cat > queries/my_query.json << EOF
{
  "query": "Are dogs allowed in public parks?",
  "filters": {
    "locations": [
      {
        "state": "ca",
        "county": ["alameda-county"]
      }
    ]
  }
}
EOF
```

2. Run with custom query:

```bash
# Update docker-compose.yml command or run directly:
docker run --gpus all \
  --env-file .env \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/queries:/app/queries:ro \
  --rm \
  rag-pipeline:latest \
  python3 main.py --mode hybrid --json queries/my_query.json
```

### Interactive Mode

```bash
# Start container in interactive mode
docker run --gpus all \
  --env-file .env \
  -v $(pwd)/outputs:/app/outputs \
  -it \
  --rm \
  rag-pipeline:latest \
  /bin/bash

# Inside container, run queries:
python3 main.py --mode hybrid --query "your query here"
```

## Step 9: Access Output Files

Output CSV files are automatically saved to the `outputs/` directory on your EC2 instance.

```bash
# View outputs
ls -lh outputs/

# Download to local machine
scp -i your-key.pem ubuntu@<EC2_IP>:~/your-repo/outputs/*.csv ./
```

## Monitoring and Troubleshooting

### Check GPU Usage

```bash
# On EC2 instance
nvidia-smi

# Inside container
docker exec rag-pipeline nvidia-smi
```

### View Container Logs

```bash
# Real-time logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100
```

### Check Container Status

```bash
docker compose ps
docker stats rag-pipeline
```

### Common Issues

**1. Out of Memory Error**
- Use larger instance (g4dn.2xlarge or g5.xlarge)
- Reduce `HYBRID_TOP_K` in `config.py`

**2. CUDA Not Available**
- Verify NVIDIA drivers: `nvidia-smi`
- Check Docker GPU access: `docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi`
- Ensure using `--gpus all` flag

**3. Model Download Timeout**
- Increase instance storage
- Check internet connectivity
- Verify HF_TOKEN has access to LLaMA models

**4. Slow First Run**
- Normal - models are downloaded on first run (~16GB)
- Subsequent runs will be faster (models are cached)

## Cost Optimization

1. **Use Spot Instances**: Save up to 70% for non-critical workloads
2. **Stop Instance When Not in Use**: You only pay for storage
3. **Use Smaller Instance for Testing**: g4dn.xlarge is sufficient for most queries
4. **Monitor Usage**: Set up CloudWatch alarms for cost tracking

## Scaling Options

### Option 1: Multiple Containers on Same Instance

```bash
# Run multiple queries in parallel
docker compose up --scale rag-pipeline=3
```

### Option 2: ECS Fargate with GPU

Deploy to AWS ECS for managed container orchestration.

### Option 3: Kubernetes (EKS)

For production-scale deployments with auto-scaling.

## Security Best Practices

1. **Restrict Security Groups**: Only allow SSH from your IP
2. **Use IAM Roles**: Instead of hardcoded credentials
3. **Encrypt Data at Rest**: Enable EBS encryption
4. **Regular Updates**: Keep Docker and system packages updated
5. **Use Secrets Manager**: For production, use AWS Secrets Manager for API keys

## Cleanup

When done, terminate resources to stop charges:

```bash
# Stop container
docker compose down

# Remove Docker image (optional)
docker rmi rag-pipeline:latest

# On AWS Console:
# - Terminate EC2 instance
# - Delete associated EBS volumes
```

## Automation Scripts

### Start on Boot

```bash
# Create systemd service
sudo nano /etc/systemd/system/rag-pipeline.service
```

Add:
```ini
[Unit]
Description=RAG Pipeline Docker Container
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/your-repo
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable rag-pipeline
sudo systemctl start rag-pipeline
```

## Support

For issues specific to:
- **EC2**: AWS Support or EC2 documentation
- **Docker**: Docker documentation
- **NVIDIA**: NVIDIA Container Toolkit documentation
- **Pipeline**: Check GitHub issues or contact your team

## Additional Resources

- [AWS EC2 GPU Instances](https://aws.amazon.com/ec2/instance-types/#Accelerated_Computing)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [Docker GPU Support](https://docs.docker.com/config/containers/resource_constraints/#gpu)
- [Hugging Face Model Hub](https://huggingface.co/models)
