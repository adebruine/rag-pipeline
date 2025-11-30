from flask import Flask, request, jsonify
from pipeline import RAGPipeline

app = Flask(__name__)

# Initialize BOTH pipelines ONCE
print("Initializing RAG Pipelines...")
baseline_pipeline = RAGPipeline(use_reranking=False)
hybrid_pipeline = RAGPipeline(use_reranking=True)
print("Pipelines ready!")

def serialize_chunks(chunks):
    """Convert retrieved chunks to JSON-serializable format."""
    serialized = []
    for chunk in chunks:
        # Create a flat dictionary for each chunk
        chunk_data = {
            'id': chunk.get('id'),
            'score': float(chunk.get('score', 0))  # Ensure it's a Python float
        }
        
        # Add rerank_score if it exists (hybrid mode)
        if 'rerank_score' in chunk:
            chunk_data['rerank_score'] = float(chunk.get('rerank_score', 0))
        
        # Add all metadata fields
        if 'metadata' in chunk:
            metadata = chunk['metadata']
            for key, value in metadata.items():
                # Convert numpy types to Python types if needed
                if hasattr(value, 'item'):  # numpy scalar
                    chunk_data[key] = value.item()
                else:
                    chunk_data[key] = value
        
        serialized.append(chunk_data)
    
    return serialized

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "gpu": "available"})

@app.route('/query', methods=['POST'])
def query():
    try:
        # Validate request has JSON data
        if not request.json:
            return jsonify({"error": "No JSON data provided"}), 400

        data = request.json

        # Extract and validate parameters
        query_text = data.get('query', '')
        filters = data.get('filters', {})
        mode = data.get('mode', 'hybrid')  # Default to hybrid

        # Validate query_text
        if not isinstance(query_text, str):
            return jsonify({"error": "query must be a string"}), 400
        if not query_text.strip():
            return jsonify({"error": "query cannot be empty"}), 400

        # Validate filters
        if not isinstance(filters, dict):
            return jsonify({"error": "filters must be a dictionary"}), 400

        # Validate mode
        if mode not in ['hybrid', 'baseline']:
            return jsonify({"error": "mode must be 'hybrid' or 'baseline'"}), 400

        # Select pipeline based on mode
        pipeline = hybrid_pipeline if mode == 'hybrid' else baseline_pipeline
        llm_output, retrieved_chunks = pipeline.run(query_text, filters)

        # Serialize chunks to JSON-safe format
        serialized_chunks = serialize_chunks(retrieved_chunks)

        return jsonify({
            "response": llm_output,
            "chunks": serialized_chunks,
            "mode": mode
        })

    except Exception as e:
        # Log the error and return a 500 response
        print(f"Error processing query: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)