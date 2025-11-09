"""
Utility functions for RAG pipeline.
"""
import pandas as pd
from typing import List, Dict, Any

from config import Config


def print_chunks(retrieved_chunks: List[dict]) -> None:
    """
    Print retrieved chunks in a formatted table.
    
    Args:
        retrieved_chunks: List of retrieved chunk dictionaries
    """
    results = []
    for c in retrieved_chunks:
        result = {}

        result['score'] = c.get('score', 0)

        metadata = c.get('metadata', {})
        result['county'] = metadata.get('county', 'N/A')
        result['section'] = metadata.get('section', 'N/A')
        result['text'] = metadata.get('chunk_text', 'N/A')

        result['penalty'] = metadata.get('penalty', 'N/A')
        result['obligation'] = metadata.get('obligation', 'N/A')
        result['permission'] = metadata.get('permission', 'N/A')
        result['prohibition'] = metadata.get('prohibition', 'N/A')
        result['fk_grade'] = metadata.get('fk_grade', 'N/A')
        result['fre'] = metadata.get('fre', 'N/A')
        result['wc'] = metadata.get('wc', 'N/A')
        result['pct_complex'] = metadata.get('pct_complex', 'N/A')

        results.append(result)

    df = pd.DataFrame(results)

    df['preview'] = df['text'].str.slice(0, 30) + '...'
    df['section'] = df['section'].str.slice(0, 20) + '...'

    output_df = df[[
        'score', 'county', 'section', 'preview', 
        'penalty', 'obligation', 'permission', 'prohibition', 
        'fk_grade', 'fre', 'wc', 'pct_complex'
    ]]

    print(f"Total number of chunks: {len(retrieved_chunks)}")
    print(output_df.to_string())


def print_chunks_reranking(retrieved_chunks: List[dict]) -> None:
    """
    Print retrieved and reranked chunks in a formatted table.
    
    Args:
        retrieved_chunks: List of retrieved chunk dictionaries with rerank scores
    """
    results = []
    for c in retrieved_chunks:
        result = {}

        result['score'] = c.get('score', 0)
        result['rerank_score'] = c.get('rerank_score', 0)

        metadata = c.get('metadata', {})
        result['county'] = metadata.get('county', 'N/A')
        result['section'] = metadata.get('section', 'N/A')
        result['text'] = metadata.get('chunk_text', 'N/A')

        result['penalty'] = metadata.get('penalty', 'N/A')
        result['obligation'] = metadata.get('obligation', 'N/A')
        result['permission'] = metadata.get('permission', 'N/A')
        result['prohibition'] = metadata.get('prohibition', 'N/A')
        result['fk_grade'] = metadata.get('fk_grade', 'N/A')
        result['fre'] = metadata.get('fre', 'N/A')
        result['wc'] = metadata.get('wc', 'N/A')
        result['pct_complex'] = metadata.get('pct_complex', 'N/A')

        results.append(result)

    df = pd.DataFrame(results)

    df['preview'] = df['text'].str.slice(0, 30) + '...'
    df['section'] = df['section'].str.slice(0, 20) + '...'

    output_df = df[[
        'score', 'rerank_score', 'county', 'section', 'preview', 
        'penalty', 'obligation', 'permission', 'prohibition', 
        'fk_grade', 'fre', 'wc', 'pct_complex'
    ]]

    print(f"Total number of chunks: {len(retrieved_chunks)}")
    print(output_df.to_string())


def generate_csv(csv_filename: str, retrieved_chunks: List[dict]) -> None:
    """
    Generate CSV file from retrieved chunks.
    
    Args:
        csv_filename: Name of the CSV file to generate
        retrieved_chunks: List of retrieved chunk dictionaries
    """
    filename = Config.get_output_path(csv_filename)

    print(f"\n--- Generating CSV File: {filename} ---")
    try:
        processed_data = []
        for chunk in retrieved_chunks:
            # Create a flat dictionary for each row
            row_data = {
                'id': chunk.get('id'),
                'score': chunk.get('score')
            }
            # Add all metadata fields as separate columns
            if 'metadata' in chunk:
                row_data.update(chunk['metadata'])
            processed_data.append(row_data)

        if not processed_data:
            print("No matches found to generate CSV.")
        else:
            # Convert to Pandas DataFrame and save to CSV
            df = pd.DataFrame(processed_data)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Successfully generated CSV with {len(df)} rows at: {filename}")

    except Exception as e:
        print(f"Error generating CSV: {e}")


def generate_csv_reranking(csv_filename: str, reranked_chunks: List[dict]) -> None:
    """
    Generate CSV file from reranked chunks (includes rerank_score).
    
    Args:
        csv_filename: Name of the CSV file to generate
        reranked_chunks: List of reranked chunk dictionaries
    """
    filename = Config.get_output_path(csv_filename)

    print(f"\n--- Generating CSV File: {filename} ---")
    try:
        processed_data = []
        for chunk in reranked_chunks:
            # Create a flat dictionary for each row
            row_data = {
                'id': chunk.get('id'),
                'score': chunk.get('score'),
                'rerank_score': chunk.get('rerank_score'),
            }
            # Add all metadata fields as separate columns
            if 'metadata' in chunk:
                row_data.update(chunk['metadata'])
            processed_data.append(row_data)

        if not processed_data:
            print("No matches found to generate CSV.")
        else:
            # Convert to Pandas DataFrame and save to CSV
            df = pd.DataFrame(processed_data)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Successfully generated CSV with {len(df)} rows at: {filename}")

    except Exception as e:
        print(f"Error generating CSV: {e}")
