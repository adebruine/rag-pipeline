"""
Retrieval functions for querying Pinecone index.
"""
from typing import Dict, List, Any, Optional
from pinecone import Pinecone
import time

from config import Config
from filters import build_pinecone_filter


def initialize_pinecone() -> tuple:
    """
    Initialize Pinecone client and index.
    
    Returns:
        Tuple of (Pinecone client, Pinecone index)
    """
    print("Initializing Pinecone...")
    pc = Pinecone(api_key=Config.PINECONE_API_KEY)
    pinecone_index = pc.Index(Config.PINECONE_INDEX_NAME)
    
    # Display index details
    index_details = pc.describe_index(Config.PINECONE_INDEX_NAME)
    print(f"Connected to index: {Config.PINECONE_INDEX_NAME}")
    print(index_details)
    
    return pc, pinecone_index


def retrieve_chunks(pc: Pinecone, pinecone_index: Any, query: str, filter_object: dict) -> dict:
    """
    Baseline retrieval: Dense embedding only.
    
    Args:
        pc: Pinecone client
        pinecone_index: Pinecone index object
        query: Query string (empty string for filter-only search)
        filter_object: Pinecone filter dictionary
        
    Returns:
        Pinecone query response
    """
    if query:
        print("Querying Pinecone...Standard Semantic Search")
        dense_query_embedding = pc.inference.embed(
            model=Config.EMBEDDING_MODEL_DENSE,
            inputs=query,
            parameters={"input_type": "query", "truncate": "END"}
        )
        query_vector = dense_query_embedding[0]['values']
        results_k = Config.BASELINE_TOP_K
    else:
        print("Querying Pinecone...Filter-Only Search")
        query_vector = [0.0] * Config.VECTOR_DIMENSION
        results_k = Config.FILTER_ONLY_TOP_K

    query_response = pinecone_index.query(
        namespace=Config.PINECONE_NAMESPACE,
        top_k=results_k,
        vector=query_vector,
        include_metadata=True,
        filter=filter_object
    )

    return query_response


def retrieve_chunks_hybrid_reranking(pc: Pinecone, pinecone_index: Any, query: str, filter_object: dict) -> dict:
    """
    Hybrid retrieval: Dense + Sparse embeddings.
    
    Args:
        pc: Pinecone client
        pinecone_index: Pinecone index object
        query: Query string (empty string for filter-only search)
        filter_object: Pinecone filter dictionary
        
    Returns:
        Pinecone query response
    """
    if query:
        print("Querying Pinecone...Hybrid Search (Dense + Sparse)")
        
        # Get dense embedding
        dense_query_embedding = pc.inference.embed(
            model=Config.EMBEDDING_MODEL_DENSE,
            inputs=query,
            parameters={"input_type": "query", "truncate": "END"}
        )
        
        # Get sparse embedding
        sparse_query_embedding = pc.inference.embed(
            model=Config.EMBEDDING_MODEL_SPARSE,
            inputs=query,
            parameters={"input_type": "query", "truncate": "END"}
        )

        dense_vector = dense_query_embedding[0]['values']
        sparse_data = sparse_query_embedding[0]  # Contains 'sparse_indices' and 'sparse_values'
        results_k = Config.HYBRID_TOP_K

        query_response = pinecone_index.query(
            namespace=Config.PINECONE_NAMESPACE,
            top_k=results_k,
            vector=dense_vector,
            sparse_vector={
                'indices': sparse_data['sparse_indices'], 
                'values': sparse_data['sparse_values']
            },
            include_values=False,
            include_metadata=True,
            filter=filter_object
        )
    else:
        print("Querying Pinecone...Filter-Only Search")
        dummy_vector = [0.0] * Config.VECTOR_DIMENSION
        results_k = Config.FILTER_ONLY_TOP_K

        query_response = pinecone_index.query(
            namespace=Config.PINECONE_NAMESPACE,
            top_k=results_k,
            vector=dummy_vector,
            include_values=False,
            include_metadata=True,
            filter=filter_object
        )

    return query_response


def run_query_for_each_location(
    pc: Pinecone, 
    pinecone_index: Any, 
    query: str, 
    filters: dict, 
    filter_only_search: bool
) -> List[dict]:
    """
    Query Pinecone for each location (state, county) pair using baseline retrieval.
    
    Args:
        pc: Pinecone client
        pinecone_index: Pinecone index object
        query: Query text
        filters: Normalized filter dictionary
        filter_only_search: Whether this is a filter-only search
        
    Returns:
        List of retrieved chunks
    """
    query_text = query
    all_filters = filters.copy()
    retrieved_chunks = []

    if filter_only_search:  # Filter-Only Search. Query with all filters.
        print("\n--- Filter-Only Search. ---")
        pinecone_filter_object = build_pinecone_filter(all_filters)
        response = retrieve_chunks(pc, pinecone_index, query_text, pinecone_filter_object)
        retrieved_chunks.extend(response.get('matches', []))
    else:  # Otherwise, query for each location.
        locations_to_search = all_filters.pop("locations", [])
        base_filters = all_filters

        print(f"\n--- Starting baseline query loop for {len(locations_to_search)} locations ---")

        for loc in locations_to_search:
            print(f"\nQuerying for location: {loc['state']}, county: {loc['county']}")

            # Build a Pinecone filter object for each location.
            loop_filter = base_filters.copy()
            loop_filter['state'] = [loc['state']]
            loop_filter['county'] = [loc['county']]
            pinecone_filter_object = build_pinecone_filter(loop_filter)

            response = retrieve_chunks(pc, pinecone_index, query_text, pinecone_filter_object)
            retrieved_chunks.extend(response.get('matches', []))

        print(f"\n--- Loop finished. Total chunks retrieved: {len(retrieved_chunks)} ---")

    return retrieved_chunks


def run_query_for_each_location_reranking(
    pc: Pinecone, 
    pinecone_index: Any, 
    reranker_model: Any,
    query: str, 
    filters: dict, 
    filter_only_search: bool
) -> List[dict]:
    """
    Query Pinecone for each location (state, county) pair using hybrid + reranking.
    
    Args:
        pc: Pinecone client
        pinecone_index: Pinecone index object
        reranker_model: CrossEncoder reranker model
        query: Query text
        filters: Normalized filter dictionary
        filter_only_search: Whether this is a filter-only search
        
    Returns:
        List of retrieved and reranked chunks
    """
    query_text = query
    all_filters = filters.copy()
    retrieved_chunks = []

    if filter_only_search:  # Filter-Only Search. Query with all filters without reranking.
        print("\n--- Filter-Only Search. ---")
        pinecone_filter_object = build_pinecone_filter(all_filters)
        response = retrieve_chunks_hybrid_reranking(pc, pinecone_index, query_text, pinecone_filter_object)
        retrieved_chunks.extend(response.get('matches', []))
    else:  # Otherwise, query for each location.
        locations_to_search = all_filters.pop("locations", [])
        base_filters = all_filters

        print(f"\n--- Starting Hybrid + Reranking query loop for {len(locations_to_search)} locations ---")

        for loc in locations_to_search:
            print(f"\nQuerying for location: {loc['state']}, county: {loc['county']}")

            # Build a filter object for each location.
            loop_filter = base_filters.copy()
            loop_filter['state'] = [loc['state']]
            loop_filter['county'] = [loc['county']]
            pinecone_filter_object = build_pinecone_filter(loop_filter)

            response = retrieve_chunks_hybrid_reranking(pc, pinecone_index, query_text, pinecone_filter_object)
            reranked_chunks = rerank_chunks(reranker_model, query, response.get('matches', []))
            retrieved_chunks.extend(reranked_chunks)

        print(f"\n--- Loop finished. Total chunks retrieved: {len(retrieved_chunks)} ---")

    return retrieved_chunks


def rerank_chunks(reranker_model: Any, query: str, pinecone_matches: List[dict], top_n: Optional[int] = None) -> List[dict]:
    """
    Reranks the retrieved chunks using a Cross-Encoder model.

    Args:
        reranker_model: CrossEncoder model
        query: The user's original query
        pinecone_matches: The list of 'matches' from Pinecone's response
        top_n: The final number of chunks to return (defaults to Config.RERANK_TOP_N)

    Returns:
        A new, sorted list of the top_n 'matches' objects
    """
    if top_n is None:
        top_n = Config.RERANK_TOP_N
        
    print(f"Reranking {len(pinecone_matches)} chunks... ")

    # Create pairs of [query, chunk_text] for the model
    pairs = []
    for match in pinecone_matches:
        chunk_text = match.get('metadata', {}).get('chunk_text', '')
        pairs.append((query, chunk_text))

    start_time = time.time()
    scores = reranker_model.predict(pairs)
    end_time = time.time()
    print(f"Reranking took {end_time - start_time:.4f} seconds")

    # Add rerank_score to original matches
    for i in range(len(scores)):
        pinecone_matches[i]['rerank_score'] = float(scores[i])

    # Sort by rerank_score
    reranked_matches = sorted(pinecone_matches, key=lambda x: x['rerank_score'], reverse=True)

    return reranked_matches[:top_n]
