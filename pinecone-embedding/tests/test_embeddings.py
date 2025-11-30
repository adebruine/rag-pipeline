import unittest
from unittest.mock import MagicMock
import polars as pl
from rag_ingest.embed_dense import embed_dense
from rag_ingest.embed_sparse import embed_sparse

class TestEmbeddings(unittest.TestCase):

    def setUp(self):
        self.mock_pc = MagicMock()
        self.df = pl.DataFrame({"chunk_text": ["doc1", "doc2"]})

    def test_embed_dense_retry_logic(self):
        """Test that dense embedding retries once on failure"""
        # First call raises Exception, Second call returns data
        self.mock_pc.inference.embed.side_effect = [
            Exception("API Error"),
            [{"values": [0.1, 0.2]}, {"values": [0.3, 0.4]}]
        ]

        res = embed_dense(self.mock_pc, self.df, text_col="chunk_text", batch_size=2)
        
        # Should have called embed twice
        self.assertEqual(self.mock_pc.inference.embed.call_count, 2)
        self.assertEqual(len(res), 2)

    def test_embed_sparse_success(self):
        """Test normal sparse embedding flow"""
        self.mock_pc.inference.embed.return_value = [
            {"sparse_indices": [1], "sparse_values": [0.5]},
            {"sparse_indices": [2], "sparse_values": [0.9]}
        ]

        res = embed_sparse(self.mock_pc, self.df, text_col="chunk_text", batch_size=2)
        
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["indices"], [1])
        self.assertEqual(res[0]["values"], [0.5])

    def test_embed_dense_batching(self):
        """Test that large inputs are batched correctly"""
        # DataFrame with 10 rows, batch_size=5 -> 2 calls
        large_df = pl.DataFrame({"chunk_text": ["row"] * 10})
        self.mock_pc.inference.embed.return_value = [{"values": []}] * 5 # return 5 items per call

        embed_dense(self.mock_pc, large_df, batch_size=5)
        
        self.assertEqual(self.mock_pc.inference.embed.call_count, 2)
