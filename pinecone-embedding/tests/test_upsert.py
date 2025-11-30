import unittest
from unittest.mock import MagicMock
from rag_ingest.upsert import upsert, build_vectors_from_df
import polars as pl


class TestUpsert(unittest.TestCase):

    def test_upsert_validation_error(self):
        """Should raise ValueError if input lists have different lengths"""
        mock_index = MagicMock()
        with self.assertRaises(ValueError):
            upsert(
                index=mock_index,
                ids=["1", "2"],
                dense_vectors=[[0.1]],  # Only 1 item
                sparse_vectors=[{}, {}],
                metadata=[{}, {}],
            )

    def test_upsert_batching(self):
        """Should verify upsert is called multiple times for large inputs"""
        mock_index = MagicMock()

        # Create 25 items
        ids = [str(i) for i in range(25)]
        dense = [[0.1] * 1024] * 25
        sparse = [{"indices": [], "values": []}] * 25
        meta = [{}] * 25

        # Set batch size to 10
        upsert(mock_index, ids, dense, sparse, meta, batch_size=10)

        # Should be called 3 times: 10, 10, 5
        self.assertEqual(mock_index.upsert.call_count, 3)

        # Verify last batch size
        args, _ = mock_index.upsert.call_args
        # args is typically passed as keyword 'vectors', so check kwargs or args[0]
        # Based on your code: index.upsert(vectors=batch)
        last_call_vectors = mock_index.upsert.call_args.kwargs["vectors"]
        self.assertEqual(len(last_call_vectors), 5)

    def test_build_vectors_mismatch(self):
        """Should raise error if DataFrame length doesn't match embeddings"""
        df = pl.DataFrame({"a": [1, 2, 3]})
        dense = [[1.0], [2.0]]  # Short
        sparse = [{}, {}]

        with self.assertRaises(ValueError):
            build_vectors_from_df(df, dense, sparse, metadata=[])


if __name__ == "__main__":
    unittest.main()
