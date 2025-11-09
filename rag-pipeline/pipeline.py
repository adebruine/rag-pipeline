"""
Main RAG pipeline orchestration.
"""
from typing import Dict, Any, Tuple, Optional

from config import Config
from models import initialize_llm, initialize_reranker
from retrieval import (
    initialize_pinecone,
    run_query_for_each_location,
    run_query_for_each_location_reranking
)
from llm_generation import (
    build_context_string,
    generate_llm_response,
    generate_llm_response_filter_only_search
)
from filters import flatten_locations_payload
from utils import (
    print_chunks,
    print_chunks_reranking,
    generate_csv,
    generate_csv_reranking
)


class RAGPipeline:
    """Main RAG Pipeline class."""
    
    def __init__(self, use_reranking: bool = False):
        """
        Initialize RAG Pipeline.
        
        Args:
            use_reranking: Whether to use hybrid search with reranking
        """
        Config.validate()
        
        self.use_reranking = use_reranking
        
        # Initialize Pinecone
        self.pc, self.pinecone_index = initialize_pinecone()
        
        # Initialize models
        print("\n" + "="*50)
        print("Initializing Models...")
        print("="*50)
        self.tokenizer, self.model = initialize_llm()
        
        if use_reranking:
            self.reranker_model = initialize_reranker()
        else:
            self.reranker_model = None
        
        print("\n" + "="*50)
        print("Pipeline Initialization Complete")
        print("="*50 + "\n")
    
    def run_baseline_search(
        self, 
        query: str, 
        filters: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Run baseline search (dense embedding only).
        
        Args:
            query: Query string (empty for filter-only search)
            filters: Filter dictionary with locations and other criteria
            
        Returns:
            Tuple of (llm_output, csv_filename)
        """
        print("\n" + "="*50)
        print("RUNNING BASELINE SEARCH")
        print("="*50)
        
        # Flatten locations
        normalized_filters = flatten_locations_payload(filters)
        
        # Determine if this is a filter-only search
        filter_only_search = not bool(query)
        
        # Run retrieval
        retrieved_chunks = run_query_for_each_location(
            self.pc,
            self.pinecone_index,
            query,
            normalized_filters,
            filter_only_search
        )
        
        # Print results
        print("\n\n--- BASELINE RESULTS ---")
        print_chunks(retrieved_chunks)
        
        # Generate output
        if query:  # Standard search
            context_string = build_context_string(retrieved_chunks)
            csv_filename = Config.BASELINE_CSV_FILENAME
            generate_csv(csv_filename, retrieved_chunks)
            llm_output = generate_llm_response(query, context_string, self.tokenizer, self.model)
        else:  # Filter-only search
            context_string = build_context_string(retrieved_chunks, 10)
            csv_filename = Config.BASELINE_FILTER_CSV_FILENAME
            generate_csv(csv_filename, retrieved_chunks)
            llm_output = generate_llm_response_filter_only_search(
                query, context_string, self.tokenizer, self.model, len(retrieved_chunks)
            )
        
        print("\n--- FINAL LLM OUTPUT ---")
        print(llm_output)
        
        return llm_output, csv_filename
    
    def run_hybrid_search(
        self, 
        query: str, 
        filters: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Run hybrid search with reranking (dense + sparse embeddings).
        
        Args:
            query: Query string (empty for filter-only search)
            filters: Filter dictionary with locations and other criteria
            
        Returns:
            Tuple of (llm_output, csv_filename)
        """
        if not self.use_reranking:
            raise ValueError("Pipeline was not initialized with reranking enabled")
        
        print("\n" + "="*50)
        print("RUNNING HYBRID SEARCH WITH RERANKING")
        print("="*50)
        
        # Flatten locations
        normalized_filters = flatten_locations_payload(filters)
        
        # Determine if this is a filter-only search
        filter_only_search = not bool(query)
        
        # Run retrieval with reranking
        retrieved_chunks = run_query_for_each_location_reranking(
            self.pc,
            self.pinecone_index,
            self.reranker_model,
            query,
            normalized_filters,
            filter_only_search
        )
        
        # Print results
        print("\n\n--- HYBRID + RERANKING RESULTS ---")
        print_chunks_reranking(retrieved_chunks)
        
        # Generate output
        if query:  # Standard search
            context_string = build_context_string(retrieved_chunks)
            csv_filename = Config.HYBRID_CSV_FILENAME
            generate_csv_reranking(csv_filename, retrieved_chunks)
            llm_output = generate_llm_response(query, context_string, self.tokenizer, self.model)
        else:  # Filter-only search
            context_string = build_context_string(retrieved_chunks, 10)
            csv_filename = Config.HYBRID_FILTER_CSV_FILENAME
            generate_csv_reranking(csv_filename, retrieved_chunks)
            llm_output = generate_llm_response_filter_only_search(
                query, context_string, self.tokenizer, self.model, len(retrieved_chunks)
            )
        
        print("\n--- FINAL LLM OUTPUT ---")
        print(llm_output)
        
        return llm_output, csv_filename
    
    def run(
        self, 
        query: str, 
        filters: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Run the appropriate search based on pipeline configuration.
        
        Args:
            query: Query string (empty for filter-only search)
            filters: Filter dictionary with locations and other criteria
            
        Returns:
            Tuple of (llm_output, csv_filename)
        """
        if self.use_reranking:
            return self.run_hybrid_search(query, filters)
        else:
            return self.run_baseline_search(query, filters)
