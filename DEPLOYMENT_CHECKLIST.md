# Deployment Checklist

Use this checklist to ensure successful deployment of the RAG pipeline on EC2.

## Pre-Deployment

- [ ] **AWS Account Setup**
  - [ ] AWS account with EC2 access
  - [ ] SSH key pair created and downloaded (.pem file)
  - [ ] Know your region (e.g., us-east-1, us-west-2)

- [ ] **API Keys Ready**
  - [ ] Pinecone API key obtained
  - [ ] Hugging Face token with LLaMA access
  - [ ] Keys stored securely

- [ ] **Code Repository**
  - [ ] Code pushed to GitHub
  - [ ] Repository URL ready
  - [ ] Or files ready to transfer via SCP

## EC2 Instance Setup

- [ ] **Launch Instance**
  - [ ] Selected GPU instance type (g4dn.xlarge minimum)
  - [ ] Used Deep Learning AMI or Ubuntu 22.04
  - [ ] Allocated 100+ GB storage
  - [ ] Security group allows SSH from your IP
  - [ ] Instance is running

- [ ] **Connect to Instance**
  - [ ] Can SSH into instance: `ssh -i key.pem ubuntu@<IP>`
  - [ ] Instance has internet access
  - [ ] Can run `nvidia-smi` (GPU visible)

## Docker Installation

- [ ] **Docker Engine**
  - [ ] Docker installed
  - [ ] User added to docker group
  - [ ] Can run `docker --version`
  - [ ] Can run `docker ps` without sudo

- [ ] **NVIDIA Container Toolkit**
  - [ ] NVIDIA toolkit installed
  - [ ] Docker restarted after installation
  - [ ] Can run: `docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi`

- [ ] **Docker Compose**
  - [ ] Docker Compose installed
  - [ ] Can run `docker compose version`

## Code Deployment

- [ ] **Get Code on EC2**
  - [ ] Repository cloned OR files transferred
  - [ ] In project directory
  - [ ] All files present (run `ls -la`)

- [ ] **Configure Environment**
  - [ ] `.env` file created from `.env.example`
  - [ ] `PINECONE_API_KEY` set in `.env`
  - [ ] `HF_TOKEN` set in `.env`
  - [ ] Scripts are executable: `chmod +x build.sh run.sh`

## Build and Run

- [ ] **Build Docker Image**
  - [ ] Run `./build.sh` or `docker build -t rag-pipeline:latest .`
  - [ ] Build completed successfully
  - [ ] Image visible: `docker images | grep rag-pipeline`

- [ ] **First Run**
  - [ ] Run `./run.sh` or `docker compose up`
  - [ ] Models downloading (this takes 10-15 min first time)
  - [ ] No CUDA errors
  - [ ] Container running: `docker compose ps`

## Verification

- [ ] **Test Queries**
  - [ ] Example query runs successfully
  - [ ] CSV file generated in `outputs/` directory
  - [ ] LLM response displayed
  - [ ] No error messages

- [ ] **Check GPU Usage**
  - [ ] Run `nvidia-smi` - GPU memory in use
  - [ ] GPU utilization > 0%

- [ ] **Review Outputs**
  - [ ] CSV files contain expected columns
  - [ ] Chunk text is readable
  - [ ] Scores make sense

## Custom Queries

- [ ] **Create Query Files**
  - [ ] `queries/` directory created
  - [ ] Custom JSON query files added
  - [ ] Query format validated

- [ ] **Run Custom Queries**
  - [ ] Can run with `--json` flag
  - [ ] Results match expectations
  - [ ] CSV outputs correct

## Production Readiness

- [ ] **Security**
  - [ ] Security group restricts SSH to known IPs
  - [ ] `.env` not committed to Git
  - [ ] API keys rotated if needed

- [ ] **Monitoring**
  - [ ] CloudWatch alarms set up (optional)
  - [ ] Cost alerts configured
  - [ ] Log monitoring in place

- [ ] **Backup**
  - [ ] Important outputs backed up
  - [ ] `.env` backed up securely
  - [ ] Configuration documented

- [ ] **Documentation**
  - [ ] Team knows how to access instance
  - [ ] Deployment steps documented
  - [ ] Troubleshooting guide available

## Optional Enhancements

- [ ] **Auto-start on Boot**
  - [ ] Systemd service created
  - [ ] Service enabled: `sudo systemctl enable rag-pipeline`
  - [ ] Tested after reboot

- [ ] **CI/CD Pipeline**
  - [ ] GitHub Actions configured
  - [ ] Automated builds
  - [ ] Automated deployment

- [ ] **API Endpoint**
  - [ ] REST API added for Streamlit
  - [ ] Security group allows API port
  - [ ] API tested

- [ ] **Scaling**
  - [ ] ECS/Kubernetes considered for scale
  - [ ] Load balancing configured
  - [ ] Auto-scaling rules set

## Cleanup (When Done)

- [ ] **Stop Services**
  - [ ] Run `docker compose down`
  - [ ] Verified container stopped

- [ ] **AWS Cleanup**
  - [ ] EC2 instance stopped or terminated
  - [ ] EBS volumes deleted (if not needed)
  - [ ] Elastic IPs released
  - [ ] Cost verified in billing dashboard

---

## Troubleshooting Reference

If you encounter issues, refer to:
1. **QUICKSTART.md** - Common issues and quick fixes
2. **EC2_SETUP.md** - Detailed troubleshooting section
3. **README.md** - Full documentation

---

## Notes

Use this section to track instance details:

- **Instance ID**: ____________________
- **Public IP**: ____________________
- **SSH Command**: `ssh -i ________.pem ubuntu@__________`
- **Region**: ____________________
- **Instance Type**: ____________________
- **Deployment Date**: ____________________
- **Deployed By**: ____________________

---

**Status**: ☐ In Progress | ☐ Testing | ☐ Production | ☐ Decommissioned
