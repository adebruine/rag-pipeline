#!/usr/bin/env python3
"""
Test script for Pinecone sparse embedding API
Save as: test_sparse_api.py
Run with: uv run python test_sparse_api.py
"""

import os
import json
from pinecone import Pinecone
from dotenv import load_dotenv


def test_sparse_embedding_api():
    """Test the Pinecone sparse embedding API with various inputs."""

    # Load environment variables
    load_dotenv()

    # Initialize Pinecone
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in environment variables")

    print(f"🔑 API Key loaded: {api_key[:10]}...")

    pc = Pinecone(api_key=api_key)

    # Test cases
    test_texts = [
        "This is a simple test sentence for sparse embedding.",
        "The quick brown fox jumps over the lazy dog. This is a longer text to test how sparse embeddings work with more content.",
        "Legal document content about municipal regulations and ordinances for testing purposes.",
        "",  # Empty string test
        "A",  # Single character test
    ]

    print("\n🧪 Testing Pinecone sparse embedding API...")
    print("=" * 60)

    for i, text in enumerate(test_texts):
        print(f"\n📝 Test {i + 1}: Text length = {len(text)}")
        print(f"Text: {repr(text[:100])}")
        print("-" * 40)

        try:
            # Make API call
            result = pc.inference.embed(
                model="pinecone-sparse-english-v0",
                inputs=[text],
                parameters={"input_type": "passage", "truncate": "END"},
            )

            print(f"✅ API call successful")
            print(f"📊 Response type: {type(result)}")
            print(f"📊 Response length: {len(result) if hasattr(result, '__len__') else 'N/A'}")

            if result:
                first_item = result[0]
                print(f"📊 First item type: {type(first_item)}")
                attributes = dir(first_item)
                print(f"📊 First item keys: {attributes}")

                # Check for sparse data
                sparse_indices = first_item.sparse_indices
                sparse_values = first_item.sparse_values

                print(f"📊 Sparse indices count: {len(sparse_indices)}")
                print(f"📊 Sparse values count: {len(sparse_values)}")

                if sparse_indices and sparse_values:
                    print(f"📊 First 5 indices: {sparse_indices[:5]}")
                    print(f"📊 First 5 values: {sparse_values[:5]}")

                    # Create the format your code expects
                    formatted_embedding = {
                        "indices": sparse_indices,
                        "values": sparse_values,
                    }
                    print(
                        f"✅ Formatted embedding: indices={len(formatted_embedding['indices'])}, values={len(formatted_embedding['values'])}")
                else:
                    print("⚠️  Empty sparse embedding returned!")

                # print the full response
                print(f"📄 Full response sample:")
                print(first_item)

        except Exception as e:
            print(f"❌ Error: {e}")
            print(f"❌ Error type: {type(e)}")

        print("\n" + "=" * 60)

    # Test batch processing
    print("\n🔄 Testing batch processing...")
    batch_texts = [
        "First document about legal regulations.",
        "Second document with municipal code information.",
        "Third document containing ordinance details."
    ]

    try:
        batch_result = pc.inference.embed(
            model="pinecone-sparse-english-v0",
            inputs=batch_texts,
            parameters={"input_type": "passage", "truncate": "END"},
        )

        print(f"✅ Batch API call successful")
        print(f"📊 Batch response length: {len(batch_result)}")

        for i, item in enumerate(batch_result):
            sparse_indices = item.sparse_indices
            sparse_values = item.sparse_values
            print(f"📊 Item {i + 1}: indices={len(sparse_indices)}, values={len(sparse_values)}")

    except Exception as e:
        print(f"❌ Batch processing error: {e}")

    print("\n🎉 Test completed!")


if __name__ == "__main__":
    test_sparse_embedding_api()