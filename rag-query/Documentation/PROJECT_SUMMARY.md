# RAG Query - Project Summary

## 🎯 What You Have

A **production-ready, Docker-containerized RAG pipeline** for legal document retrieval that runs on AWS EC2 with GPU support.

---

## 📦 Complete File List

**All files located in**: `rag-query/` directory

### Core Python Files (9)
```
✓ rag-query/api.py               - Flask REST API (returns JSON to frontend)
✓ rag-query/config.py            - Configuration & environment variables
✓ rag-query/models.py            - LLM & reranker initialization
✓ rag-query/filters.py           - Filter processing utilities
✓ rag-query/retrieval.py         - Pinecone retrieval (baseline & hybrid)
✓ rag-query/llm_generation.py    - LLM response generation
✓ rag-query/utils.py             - Utility functions
✓ rag-query/pipeline.py          - Main pipeline orchestration
✓ rag-query/main.py              - CLI entry point
```

### Docker Files (6)
```
✓ rag-query/Dockerfile             - Container image definition
✓ rag-query/docker-compose.yml     - Container orchestration
✓ rag-query/.dockerignore          - Build optimization
✓ rag-query/build.sh               - Build automation script
✓ rag-query/run.sh                 - Run automation script
✓ rag-query/.env.example           - Environment template
```

### Documentation (5)
```
✓ rag-query/README.md                    - Complete documentation
✓ rag-query/EC2_SETUP.md                 - Detailed EC2 guide
✓ rag-query/QUICKSTART.md                - 5-minute deployment
✓ rag-query/DEPLOYMENT_CHECKLIST.md      - Step-by-step checklist
✓ rag-query/PROJECT_SUMMARY.md           - This file
```

### Configuration Files (3)
```
✓ rag-query/requirements.txt       - Python dependencies
✓ rag-query/example_query.json     - Example query format
✓ rag-query/.gitignore             - Git exclusions
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
3. Navigate to rag-query/
   │
   ▼
4. Set .env Variables
   │
   ▼
5. Build Docker Image (./build.sh)
   │
   ▼
6. Run Container (./run.sh or docker compose up)
   │
   ▼
7. Models Download (First run only - ~16GB)
   │
   ▼
8. Flask API Ready on port 8000! ✓
   │
   ▼
9. Test: curl http://localhost:8000/health
```

---

## 🎮 Usage Modes

### API Mode (Recommended - Returns JSON)
```bash
cd rag-query

# Start the Flask API server
docker compose up -d

# Query via API (returns JSON)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are dog walking regulations?",
    "filters": {
      "locations": [{"state": "ca", "county": ["alameda-county"]}]
    },
    "mode": "hybrid"
  }'
```
**Output**: JSON response with `response` and `chunks` fields

### CLI Mode (For Testing - Can save to CSV)
```bash
cd rag-query

# Baseline search
python main.py --mode baseline --example

# Hybrid search
python main.py --mode hybrid --example

# Filter-only search
python main.py --mode hybrid --json queries/filter_only.json
```
**Note**: CLI mode can generate CSV files if enabled in pipeline.py (currently disabled)

---

## 📊 Input/Output

### API Input (POST /query)
```json
{
  "query": "Are dogs allowed in public parks?",
  "filters": {
    "locations": [
      {"state": "ca", "county": ["alameda-county"]}]
    ],
    "penalty": "Y"
  },
  "mode": "hybrid"
}
```

### API Output (JSON)
```json
{
  "response": "Based on the retrieved legal documents, dogs are allowed in public parks in Alameda County with the following restrictions...",
  "chunks": [
    {
      "id": "chunk_123",
      "score": 0.856,
      "rerank_score": 0.923,
      "state": "ca",
      "county": "alameda-county",
      "section": "Chapter 6.04.010",
      "chunk_text": "Full legal text of the regulation...",
      "penalty": "Y",
      "obligation": "Y",
      "permission": "N",
      "prohibition": "Y",
      "fk_grade": 12.5,
      "fre": 45.2,
      "wc": 250,
      "pct_complex": 35.8
    }
  ],
  "mode": "hybrid"
}
```

**Frontend can convert `chunks` array to CSV/DataFrame for display and download**

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

- ✅ **REST API**: Flask API returns JSON for easy frontend integration
- ✅ **Dual Pipeline**: Baseline and Hybrid modes initialized once
- ✅ **Modular Design**: Easy to modify and extend
- ✅ **Docker-First**: Consistent environment everywhere
- ✅ **GPU Optimized**: 4-bit quantization for efficiency
- ✅ **Production Ready**: Error handling, logging, validation
- ✅ **Flexible Filtering**: 10+ filter types supported
- ✅ **JSON Response**: Returns LLM response + structured chunk data
- ✅ **Two Search Modes**: Baseline and Hybrid with reranking
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

Your pipeline exposes a Flask REST API that returns JSON data for frontend consumption:

```python
# In your Streamlit app
import requests
import pandas as pd
import streamlit as st

# API endpoint (EC2 public IP or localhost)
API_URL = "http://your-ec2-ip:8000"

def run_rag_query(query, filters, mode="hybrid"):
    """Call RAG API and return results."""
    response = requests.post(
        f"{API_URL}/query",
        json={
            "query": query,
            "filters": filters,
            "mode": mode
        },
        timeout=300
    )

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code}")
        return None

# In Streamlit UI
query = st.text_input("Enter your query")
mode = st.radio("Mode", ["hybrid", "baseline"])

if st.button("Search"):
    result = run_rag_query(query, {}, mode=mode)

    if result:
        # Display LLM response
        st.subheader("AI Response")
        st.write(result["response"])

        # Display retrieved chunks as dataframe
        st.subheader("Retrieved Documents")
        df = pd.DataFrame(result["chunks"])
        st.dataframe(df)

        # Download as CSV (client-side conversion)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "results.csv")
```

**API Response Format:**
```json
{
  "response": "LLM-generated answer...",
  "chunks": [
    {
      "id": "chunk_123",
      "score": 0.85,
      "rerank_score": 0.92,
      "state": "ca",
      "county": "alameda-county",
      "chunk_text": "Full legal text...",
      ...
    }
  ],
  "mode": "hybrid"
}
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
