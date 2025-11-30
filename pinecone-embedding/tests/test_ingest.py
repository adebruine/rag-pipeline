import unittest
from unittest.mock import patch, MagicMock
import polars as pl

# Import the main module to test
# Ensure your PYTHONPATH includes 'src' or install the package in editable mode
from rag_ingest import ingest


class TestIngestPipeline(unittest.TestCase):

    @patch("rag_ingest.ingest.upsert")
    @patch("rag_ingest.ingest.build_vectors_from_df")
    @patch("rag_ingest.ingest.embed_sparse")
    @patch("rag_ingest.ingest.embed_dense")
    @patch("rag_ingest.ingest.load_parquet_from_s3")
    @patch("rag_ingest.ingest.init_pinecone")
    @patch("rag_ingest.ingest.parse_args")
    def test_main_execution_flow(
        self,
        mock_parse_args,
        mock_init_pinecone,
        mock_load_parquet,
        mock_embed_dense,
        mock_embed_sparse,
        mock_build_vectors,
        mock_upsert,
    ):
        # --- 1. Setup Mocks ---

        # Mock command line args
        mock_args = MagicMock()
        mock_args.index_name = "test-index"
        mock_args.bucket = "test-bucket"
        mock_args.prefix = "data/"
        mock_args.single_key = None
        mock_args.metadata_cols = ["county", "state"]
        mock_parse_args.return_value = mock_args

        # Mock Pinecone Client & Index
        mock_pc = MagicMock()
        mock_index = MagicMock()
        mock_init_pinecone.return_value = (mock_pc, mock_index)

        # Mock DataFrame returning from S3 loader
        # Create a tiny fake DataFrame
        fake_df = pl.DataFrame(
            {
                "chunk_text": ["hello world", "test data"],
                "county": ["Alameda", "San Francisco"],
                "state": ["CA", "CA"],
            }
        )
        mock_load_parquet.return_value = fake_df

        # Mock Embeddings
        mock_embed_dense.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_embed_sparse.return_value = [
            {"indices": [1, 2], "values": [0.5, 0.6]},
            {"indices": [3, 4], "values": [0.7, 0.8]},
        ]

        # Mock Vector Builder
        # (vectors, ids)
        fake_vectors = [
            {"id": "1", "metadata": {"county": "Alameda"}, "values": [0.1, 0.2]},
            {"id": "2", "metadata": {"county": "San Francisco"}, "values": [0.3, 0.4]},
        ]
        fake_ids = ["1", "2"]
        mock_build_vectors.return_value = (fake_vectors, fake_ids)

        # Mock Upsert stats return
        mock_upsert.return_value = {"upserted_count": 2}

        # --- 2. Execute Code Under Test ---
        ingest.main()

        # --- 3. Assertions ---

        # Verify Init
        mock_init_pinecone.assert_called_once_with(
            index_name="test-index", dimension=1024, region="us-east-1"
        )

        # Verify S3 Load
        mock_load_parquet.assert_called_once_with(
            bucket="test-bucket", prefix="data/", single_key=None, region="us-east-1"
        )

        # Verify Embed Dense
        mock_embed_dense.assert_called_once()
        # Check that the DF passed to embed_dense is our fake_df
        call_args = mock_embed_dense.call_args
        self.assertTrue(call_args.kwargs["df"].equals(fake_df))

        # Verify Embed Sparse
        mock_embed_sparse.assert_called_once()

        # Verify Build Vectors
        mock_build_vectors.assert_called_once()
        self.assertEqual(
            mock_build_vectors.call_args.kwargs["metadata"], ["county", "state"]
        )

        # Verify Upsert
        # We want to make sure the 'metadata' list passed to upsert matches what we expect
        expected_metadata_list = [{"county": "Alameda"}, {"county": "San Francisco"}]

        mock_upsert.assert_called_once()
        upsert_kwargs = mock_upsert.call_args.kwargs

        self.assertEqual(upsert_kwargs["ids"], fake_ids)
        self.assertEqual(upsert_kwargs["index"], mock_index)
        self.assertEqual(upsert_kwargs["metadata"], expected_metadata_list)

        print("\nTest Passed: Ingest pipeline flow verified.")


if __name__ == "__main__":
    unittest.main()
