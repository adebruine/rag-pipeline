"""
Main entry point for RAG pipeline execution.
"""
import argparse
import json
from typing import Dict, Any

from pipeline import RAGPipeline


def load_query_from_json(filepath: str) -> Dict[str, Any]:
    """
    Load query and filters from a JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Dictionary with 'query' and 'filters' keys
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data


def run_example():
    """Run an example query with mock data."""
    # Example query and filters (from the notebook)
    query_text = "which counties have laws about dogs?"
    
    filters = {
        "locations": [
            {
                "state": "ca",
                "county": ["alameda-county", "butte-county", "calaveras-county"]
            },
            {
                "state": "ga",
                "county": ["fulton-county"]
            },
            {
                "state": "fl",
                "county": ["alachua-county"]
            }
        ],
        # Optional filters (uncomment to use):
        # "penalty": 'Y',
        # "obligation": 'Y',
        # "permission": 'Y',
        # "prohibition": 'Y',
        # "fk_grade": {"min": 5.0, "max": 50.0},
        # "fre": {"min": 10.0, "max": 100.0},
        # "wc": {"min": 100, "max": 500},
        # "pct_complex": {"min": 10, "max": 50}
    }
    
    return query_text, filters


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Run RAG Pipeline')
    parser.add_argument(
        '--mode',
        type=str,
        choices=['baseline', 'hybrid'],
        default='baseline',
        help='Search mode: baseline (dense only) or hybrid (dense+sparse+reranking)'
    )
    parser.add_argument(
        '--query',
        type=str,
        default=None,
        help='Query string (leave empty for filter-only search)'
    )
    parser.add_argument(
        '--json',
        type=str,
        default=None,
        help='Path to JSON file with query and filters'
    )
    parser.add_argument(
        '--example',
        action='store_true',
        help='Run with example query from notebook'
    )
    
    args = parser.parse_args()
    
    # Determine query and filters
    if args.json:
        print(f"Loading query from JSON file: {args.json}")
        data = load_query_from_json(args.json)
        query = data.get('query', '')
        filters = data.get('filters', {})
    elif args.example:
        print("Running example query from notebook...")
        query, filters = run_example()
    elif args.query is not None:
        # If query provided via CLI, use default filters
        query = args.query
        filters = {
            "locations": [
                {
                    "state": "ca",
                    "county": ["alameda-county"]
                }
            ]
        }
    else:
        print("No query provided. Running example...")
        query, filters = run_example()
    
    # Initialize pipeline
    use_reranking = (args.mode == 'hybrid')
    pipeline = RAGPipeline(use_reranking=use_reranking)
    
    # Run pipeline
    llm_output, csv_filename = pipeline.run(query, filters)
    
    print("\n" + "="*50)
    print("PIPELINE EXECUTION COMPLETE")
    print("="*50)
    print(f"CSV saved to: {csv_filename}")
    print(f"LLM Output:\n{llm_output}")


if __name__ == "__main__":
    main()
