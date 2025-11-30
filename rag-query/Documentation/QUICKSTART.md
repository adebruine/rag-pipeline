# Quick Start Guide - Docker Deployment on EC2

This is the **fastest way** to get your RAG Query API running on AWS EC2.

## 🚀 5-Minute Deployment

### Step 1: Launch EC2 Instance (2 min)

1. Go to AWS EC2 Console
2. Click "Launch Instance"
3. Select: **Deep Learning AMI GPU PyTorch (Ubuntu 22.04)**
4. Choose: **g4dn.xlarge** (or larger)
5. Storage: **100 GB**
6. **Security Group**: Allow inbound on port **8000** (for Flask API)
7. Launch and download your `.pem` key

### Step 2: Connect & Setup (2 min)

```bash
# SSH into your instance
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>

# Install Docker (one command)
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo usermod -aG docker ubuntu && newgrp docker

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) && \
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add - && \
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list && \
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit && \
sudo systemctl restart docker

# Install Docker Compose
sudo apt-get install -y docker-compose-plugin
```

### Step 3: Deploy Your Code (1 min)

```bash
# Clone your repo
git clone https://github.com/your-username/your-repo.git
cd your-repo/rag-query

# Set up environment
cp .env.example .env
nano .env  # Add: PINECONE_API_KEY=xxx and HF_TOKEN=xxx
# Save: Ctrl+X, Y, Enter

# Build and run Flask API
./build.sh && ./run.sh
# or
docker compose up -d
```

### Step 4: Test the API

```bash
# Check health
curl http://localhost:8000/health

# Test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are dog regulations?", "filters": {}, "mode": "hybrid"}'
```

**That's it!** Your Flask API is now running on port 8000! 🎉

---

## 📋 What You Need Before Starting

- [ ] AWS Account
- [ ] Pinecone API Key ([get one here](https://www.pinecone.io/))
- [ ] Hugging Face Token ([get one here](https://huggingface.co/settings/tokens))
- [ ] Your GitHub repo URL

---

## 🎯 Common Commands

```bash
# Check if GPU is accessible
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Start Flask API in background
docker compose up -d

# View logs
docker compose logs -f

# Stop container
docker compose down

# Query the API (from EC2 or remote)
curl -X POST http://<EC2_PUBLIC_IP>:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Your question here",
    "filters": {"locations": [{"state": "ca", "county": ["alameda-county"]}]},
    "mode": "hybrid"
  }'

# CLI mode (for testing)
docker run --gpus all --env-file .env \
  rag-pipeline:latest \
  python3 main.py --mode hybrid --example
```

---

## 💰 Cost Estimate

**g4dn.xlarge** (recommended minimum):
- ~$0.526/hour
- ~$12.62/day (if running 24/7)
- Stop when not in use to save money!

**Pro Tip**: Use Spot Instances for up to 70% savings!

---

## 🔧 Troubleshooting

### "Cannot connect to Docker daemon"
```bash
sudo systemctl start docker
sudo systemctl status docker
```

### "GPU not found"
```bash
nvidia-smi  # Should show your GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### "Permission denied" on build.sh
```bash
chmod +x build.sh run.sh
```

### Out of Memory
- Use larger instance: `g4dn.2xlarge` or `g5.xlarge`
- Reduce `HYBRID_TOP_K` in `config.py`

---

## 📁 Getting Your Results

### API returns JSON:
```bash
# Query from your local machine
curl -X POST http://<EC2_PUBLIC_IP>:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "dog laws", "filters": {}, "mode": "hybrid"}' \
  | jq '.'  # Pretty print JSON
```

### Response format:
```json
{
  "response": "LLM-generated answer...",
  "chunks": [
    {"id": "...", "score": 0.85, "chunk_text": "..."},
    ...
  ],
  "mode": "hybrid"
}
```

**Frontend apps** (like Streamlit) can convert the `chunks` array to CSV/DataFrame for display and download.

---

## 🎓 Next Steps

- Read **[EC2_SETUP.md](EC2_SETUP.md)** for detailed instructions
- Read **[../README.md](../README.md)** for all features and configuration
- Read **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** for architecture overview
- Modify `config.py` to customize behavior
- Connect your Streamlit frontend to the API

---

## 📞 Need Help?

1. Check the logs: `docker compose logs -f`
2. Verify GPU: `nvidia-smi`
3. Check container status: `docker compose ps`
4. Review **EC2_SETUP.md** troubleshooting section

---

## 🛑 When You're Done

**Don't forget to stop your EC2 instance to avoid charges!**

```bash
# On your EC2 instance
docker compose down

# Then in AWS Console
# EC2 → Instances → Select your instance → Stop (or Terminate)
```

---

**Happy Querying! 🚀**
