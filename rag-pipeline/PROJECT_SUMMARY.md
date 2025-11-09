# RAG Pipeline - Project Summary

## 🎯 What You Have

A **production-ready, Docker-containerized RAG pipeline** for legal document retrieval that runs on AWS EC2 with GPU support.

---

## 📦 Complete File List (18 files)

### Core Python Files (8)
```
✓ config.py              - Configuration & environment variables
✓ models.py              - LLM & reranker initialization  
✓ filters.py             - Filter processing utilities
✓ retrieval.py           - Pinecone retrieval (baseline & hybrid)
✓ llm_generation.py      - LLM response generation
✓ utils.py               - CSV export & printing utilities
✓ pipeline.py            - Main pipeline orchestration
✓ main.py                - Entry point with CLI
```

### Docker Files (6)
```
✓ Dockerfile             - Container image definition
✓ docker-compose.yml     - Container orchestration
✓ .dockerignore          - Build optimization
✓ build.sh               - Build automation script
✓ run.sh                 - Run automation script  
✓ .env.example           - Environment template
```

### Documentation (4)
```
✓ README.md                    - Complete documentation
✓ EC2_SETUP.md                 - Detailed EC2 guide
✓ QUICKSTART.md                - 5-minute deployment
✓ DEPLOYMENT_CHECKLIST.md      - Step-by-step checklist
```

### Configuration Files (3)
```
✓ requirements.txt       - Python dependencies
✓ example_query.json     - Example query format
✓ .gitignore            - Git exclusions
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS EC2 GPU Instance                  │
│                         (g4dn.xlarge)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Docker Container                          │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │         RAG Pipeline Application                 │  │  │
│  │  │                                                   │  │  │
│  │  │  ┌──────────────┐    ┌──────────────┐          │  │  │
│  │  │  │   LLaMA 3.1  │    │  Reranker    │          │  │  │
│  │  │  │   8B Model   │    │   Model      │          │  │  │
│  │  │  └──────────────┘    └──────────────┘          │  │  │
│  │  │           │                  │                   │  │  │
│  │  │           └──────────────────┘                   │  │  │
│  │  │                    │                             │  │  │
│  │  │         ┌──────────▼──────────┐                 │  │  │
│  │  │         │   Pipeline Core     │                 │  │  │
│  │  │         │  • Retrieval        │                 │  │  │
│  │  │         │  • Filtering        │                 │  │  │
│  │  │         │  • Generation       │                 │  │  │
│  │  │         └──────────┬──────────┘                 │  │  │
│  │  │                    │                             │  │  │
│  │  └────────────────────┼─────────────────────────────┘  │  │
│  │                       │                                 │  │
│  └───────────────────────┼─────────────────────────────────┘  │
│                          │                                     │
│                 ┌────────▼────────┐                           │
│                 │  outputs/ dir   │                           │
│                 │  (Volume Mount) │                           │
│                 └─────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Pinecone Vector DB  │
              │  (Cloud - External)   │
              └───────────────────────┘
```

---

## 🚀 Deployment Flow

```
1. GitHub Push
   │
   ▼
2. Clone on EC2
   │
   ▼
3. Set .env Variables
   │
   ▼
4. Build Docker Image (./build.sh)
   │
   ▼
5. Run Container (./run.sh)
   │
   ▼
6. Models Download (First run only)
   │
   ▼
7. Pipeline Ready! ✓
```

---

## 🎮 Usage Modes

### Mode 1: Baseline Search (Dense Embedding Only)
```bash
docker compose up
# or
python main.py --mode baseline --example
```
**Output**: `baseline_retrieval_output.csv`

### Mode 2: Hybrid Search (Dense + Sparse + Reranking)
```bash
docker run --gpus all --env-file .env \
  -v $(pwd)/outputs:/app/outputs \
  rag-pipeline:latest \
  python3 main.py --mode hybrid --example
```
**Output**: `hybrid_retrieval_output.csv`

### Mode 3: Filter-Only Search
```bash
# Set query to empty string in JSON
python main.py --mode hybrid --json queries/filter_only.json
```
**Output**: `hybrid_filter_only_output.csv`

---

## 📊 Input/Output

### Input
```json
{
  "query": "Are dogs allowed in public parks?",
  "filters": {
    "locations": [
      {"state": "ca", "county": ["alameda-county"]}
    ],
    "penalty": "Y"
  }
}
```

### Output (CSV)
| Column | Description |
|--------|-------------|
| id | Document ID |
| score | Similarity score |
| rerank_score | Reranker score (hybrid mode) |
| state | State code |
| county | County name |
| section | Legal section reference |
| chunk_text | Full text of law snippet |
| penalty, obligation, etc. | Binary tags |
| fk_grade, fre, wc | Readability metrics |

**Plus**: LLM-generated natural language summary

---

## 💰 Cost Breakdown

### EC2 Costs (g4dn.xlarge in us-east-1)
- **On-Demand**: ~$0.526/hour
- **24/7 Monthly**: ~$379.22
- **8 hours/day**: ~$126.41/month
- **Spot Instance**: 60-70% cheaper!

### API Costs
- **Pinecone**: Varies by usage (check your plan)
- **Hugging Face**: Free (you host the model)

**Cost-Saving Tips:**
1. Stop instance when not in use
2. Use Spot instances for batch jobs
3. Consider reserved instances for long-term

---

## 🔧 Key Features

- ✅ **Modular Design**: Easy to modify and extend
- ✅ **Docker-First**: Consistent environment everywhere
- ✅ **GPU Optimized**: 4-bit quantization for efficiency
- ✅ **Production Ready**: Error handling, logging, validation
- ✅ **Flexible Filtering**: 10+ filter types supported
- ✅ **CSV Export**: Ready for Streamlit or other frontends
- ✅ **Two Search Modes**: Baseline and Hybrid with reranking
- ✅ **Batch Processing**: Process multiple queries in queue
- ✅ **Easy Deployment**: One command build and run

---

## 📚 Documentation Guide

**Start here:**
1. 📖 **QUICKSTART.md** - Get running in 5 minutes
2. 📋 **DEPLOYMENT_CHECKLIST.md** - Track your progress
3. 📘 **EC2_SETUP.md** - Detailed setup instructions
4. 📕 **README.md** - Complete reference

---

## 🔌 Integration with Streamlit

Your pipeline outputs CSV files that can be directly consumed by Streamlit:

```python
# In your Streamlit app
import subprocess
import pandas as pd

def run_rag_query(query, filters):
    # Option 1: Call via API (TODO: add API layer)
    # Option 2: Run Docker container
    subprocess.run([
        "docker", "run", "--gpus", "all",
        "--env-file", ".env",
        "-v", "$(pwd)/outputs:/app/outputs",
        "rag-pipeline:latest",
        "python3", "main.py", "--mode", "hybrid",
        "--query", query
    ])
    
    # Read results
    df = pd.read_csv("outputs/hybrid_retrieval_output.csv")
    return df

# In Streamlit
df = run_rag_query(user_query, user_filters)
st.dataframe(df)
```

---

## 🎯 Next Steps

1. **Deploy to EC2** - Follow QUICKSTART.md
2. **Test with Your Data** - Run example queries
3. **Integrate with Frontend** - Connect to Streamlit
4. **Scale as Needed** - Add more instances or move to ECS
5. **Monitor Costs** - Set up billing alerts

---

## ✅ What Makes This Production-Ready

- ✅ Environment variable configuration
- ✅ Error handling throughout
- ✅ Docker containerization
- ✅ GPU optimization
- ✅ Modular, testable code
- ✅ Comprehensive documentation
- ✅ Deployment automation
- ✅ Volume mounts for persistence
- ✅ Multiple usage modes
- ✅ CSV export for integration

---

## 🤝 Support

**For Issues:**
1. Check troubleshooting in EC2_SETUP.md
2. Review container logs: `docker compose logs -f`
3. Verify GPU access: `nvidia-smi`
4. Check API keys in .env

**Resources:**
- AWS EC2 Documentation
- Docker Documentation  
- Pinecone Documentation
- Hugging Face Hub

---

## 📝 Version Info

- **Pipeline Version**: 1.0.0
- **LLM Model**: meta-llama/Llama-3.1-8B-Instruct
- **Embedding**: Pinecone llama-text-embed-v2 + sparse
- **Reranker**: cross-encoder/ms-marco-MiniLM-L-6-v2
- **Python**: 3.10+
- **CUDA**: 12.1+
- **Docker**: 20.10+

---

**Ready to deploy? Start with QUICKSTART.md! 🚀**
