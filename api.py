from flask import Flask, request, jsonify
from pipeline import RAGPipeline

app = Flask(__name__)

# Initialize BOTH pipelines ONCE
print("Initializing RAG Pipelines...")
baseline_pipeline = RAGPipeline(use_reranking=False)
hybrid_pipeline = RAGPipeline(use_reranking=True)
print("Pipelines ready!")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "gpu": "available"})

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    query_text = data.get('query', '')
    filters = data.get('filters', {})
    mode = data.get('mode', 'hybrid')  # Default to hybrid
    
    # Select pipeline based on mode
    pipeline = hybrid_pipeline if mode == 'hybrid' else baseline_pipeline
    llm_output, retrieved_chunks = pipeline.run(query_text, filters)
    
    return jsonify({
        "response": llm_output,
        "chunks": retrieved_chunks,
        "mode": mode
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)