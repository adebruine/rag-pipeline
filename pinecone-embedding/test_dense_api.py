#!/usr/bin/env python3
"""
Test script for Pinecone dense embedding API
Save as: test_dense_api.py
Run with: uv run python test_dense_api.py
"""

import os
from pinecone import Pinecone
from dotenv import load_dotenv


def test_dense_embedding_api():
    """Test the Pinecone dense embedding API with various inputs."""

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
        "This is a simple test sentence for dense embedding.",
        "The quick brown fox jumps over the lazy dog. This is a longer text to test how dense embeddings work with more content.",
        "Legal document content about municipal regulations and ordinances for testing purposes.",
        "",  # Empty string test
        "A",  # Single character test
    ]

    print("\n🧪 Testing Pinecone dense embedding API...")
    print("=" * 60)

    for i, text in enumerate(test_texts):
        print(f"\n📝 Test {i + 1}: Text length = {len(text)}")
        print(f"Text: {repr(text[:100])}")
        print("-" * 40)

        try:
            result = pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=[text],
                parameters={"input_type": "passage", "truncate": "END"},
            )

            print(f"✅ API call successful")
            print(f"📊 Response type: {type(result)}")
            print(f"📊 Response length: {len(result) if hasattr(result, '__len__') else 'N/A'}")

            if result:
                first_item = result[0]
                print(f"📊 First item type: {type(first_item)}")
                print(f"📊 First item keys: {dir(first_item)}")

                values = first_item.values

                print(f"📊 Embedding dimensions: {len(values)}")
                print(f"📊 First 5 values: {values[:5]}")
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
            model="llama-text-embed-v2",
            inputs=batch_texts,
            parameters={"input_type": "passage", "truncate": "END"},
        )

        print(f"✅ Batch API call successful")
        print(f"📊 Batch response length: {len(batch_result)}")

        for i, item in enumerate(batch_result):
            values = item.values
            print(f"📊 Item {i + 1}: dimensions={len(values)}, first value={values[0]:.6f}")

    except Exception as e:
        print(f"❌ Batch processing error: {e}")

    print("\n🎉 Test completed!")


if __name__ == "__main__":
    test_dense_embedding_api()