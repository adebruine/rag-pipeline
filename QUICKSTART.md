# Quick Start Guide - Docker Deployment on EC2

This is the **fastest way** to get your RAG pipeline running on AWS EC2.

## 🚀 5-Minute Deployment

### Step 1: Launch EC2 Instance (2 min)

1. Go to AWS EC2 Console
2. Click "Launch Instance"
3. Select: **Deep Learning AMI GPU PyTorch (Ubuntu 22.04)**
4. Choose: **g4dn.xlarge** (or larger)
5. Storage: **100 GB**
6. Launch and download your `.pem` key

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
cd your-repo

# Set up environment
cp .env.example .env
nano .env  # Add: PINECONE_API_KEY=xxx and HF_TOKEN=xxx
# Save: Ctrl+X, Y, Enter

# Build and run
./build.sh && ./run.sh
```

**That's it!** Your pipeline is now running. 🎉

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

# Run in background
docker compose up -d

# View logs
docker compose logs -f

# Stop container
docker compose down

# Run custom query
docker run --gpus all --env-file .env \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/queries:/app/queries:ro \
  rag-pipeline:latest \
  python3 main.py --mode hybrid --json queries/my_query.json

# Access outputs
ls outputs/
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

### Download CSV files to your local machine:
```bash
# From your local terminal (not EC2)
scp -i your-key.pem ubuntu@<EC2_IP>:~/your-repo/outputs/*.csv ./
```

### Or view on EC2:
```bash
cd outputs/
ls -lh
cat baseline_retrieval_output.csv | head
```

---

## 🎓 Next Steps

- Read **[EC2_SETUP.md](EC2_SETUP.md)** for detailed instructions
- Read **[README.md](README.md)** for all features and configuration
- Modify `config.py` to customize behavior
- Create custom query files in `queries/` directory

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
