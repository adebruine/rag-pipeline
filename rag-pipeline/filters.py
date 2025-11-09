"""
Filter processing utilities for RAG pipeline.
"""
from typing import Dict, List, Any


def flatten_locations_payload(filters_payload: dict) -> dict:
    """
    Normalizes a nested filters payload. It takes a 'locations' key
    that has lists of counties and flattens it into a simple
    list of {state, county} pairs.
    
    Args:
        filters_payload: Dictionary with nested location structure
        
    Returns:
        Dictionary with flattened location list
    """
    normalized_filters = filters_payload.copy()
    nested_locations = normalized_filters.pop("locations", [])

    flat_locations = []
    if nested_locations:
        print("\n--- Flattening nested location payload ---")
        for loc_group in nested_locations:
            state = loc_group['state']
            for county in loc_group['county']:
                flat_locations.append({"state": state, "county": county})
                print(f"Added to queue: (state={state}, county={county})")

    # Add flattened list back into the filters
    normalized_filters['locations'] = flat_locations

    return normalized_filters


def build_pinecone_filter(frontend_filters: dict) -> dict:
    """
    Converts a JSON filter object from the frontend into a
    Pinecone-compatible metadata filter dictionary.
    
    Args:
        frontend_filters: Dictionary containing filter criteria
        
    Returns:
        Pinecone-compatible filter dictionary
    """
    multi_select_fields = ['state', 'county']
    binary_fields = ['penalty', 'obligation', 'permission', 'prohibition']
    numeric_fields = ['fk_grade', 'fre', 'wc', 'pct_complex']

    pinecone_filter = {}
    for key, value in frontend_filters.items():
        # --- Handle Multi-Select fields (e.g., state, county) ---
        if key in multi_select_fields:
            if isinstance(value, list) and len(value) > 0:
                pinecone_filter[key] = {"$in": value}

        # --- Handle Binary Y/N fields ---
        elif key in binary_fields:
            if value in ('Y', 'N'):
                pinecone_filter[key] = {"$eq": value}

        # --- Handle Numeric fields ---
        elif key in numeric_fields:
            range_query = {}
            if 'min' in value and value['min'] is not None:
                range_query["$gte"] = value['min']
            if 'max' in value and value['max'] is not None:
                range_query["$lte"] = value['max']

            if range_query:  # Only add if min or max was set
                pinecone_filter[key] = range_query

    return pinecone_filter
