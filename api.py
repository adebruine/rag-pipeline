from flask import Flask, request, jsonify, send_file
from pipeline import RAGPipeline
import os

app = Flask(__name__)

# Initialize pipeline ONCE when container starts
print("Initializing RAG Pipeline...")
pipeline = RAGPipeline(use_reranking=True)
print("Pipeline ready!")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "gpu": "available"})

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    query_text = data.get('query', '')
    filters = data.get('filters', {})
    
    # Run pipeline
    llm_output, csv_filename = pipeline.run(query_text, filters)
    
    return jsonify({
        "response": llm_output,
        "csv_file": csv_filename
    })

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    filepath = f"outputs/{filename}"
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)