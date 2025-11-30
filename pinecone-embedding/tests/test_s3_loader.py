import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO
import polars as pl
from rag_ingest.s3_loader import load_parquet_from_s3

class TestS3Loader(unittest.TestCase):

    @patch('boto3.client')
    def test_single_file_load(self, mock_boto):
        """Test loading a single specific key"""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        # Mock S3 response body
        # Create a real small parquet in memory to return
        df = pl.DataFrame({"col1": [1, 2]})
        buf = BytesIO()
        df.write_parquet(buf)
        buf.seek(0)
        
        mock_s3.get_object.return_value = {'Body': MagicMock(read=lambda: buf.getvalue())}

        result = load_parquet_from_s3("bucket", single_key="file.parquet")
        
        mock_s3.get_object.assert_called_with(Bucket="bucket", Key="file.parquet")
        self.assertTrue(result.equals(df))

    @patch('boto3.client')
    def test_multiple_files_pagination(self, mock_boto):
        """Test loading multiple files with pagination"""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        # Setup Pagination responses
        # Page 1: file1.parquet, NextToken present
        # Page 2: file2.parquet, No NextToken
        mock_s3.list_objects_v2.side_effect = [
            {
                "Contents": [{"Key": "file1.parquet"}],
                "IsTruncated": True,
                "NextContinuationToken": "token123"
            },
            {
                "Contents": [{"Key": "file2.parquet"}],
                "IsTruncated": False
            }
        ]

        # Mock get_object to return valid parquet bytes
        df = pl.DataFrame({"col1": [1]})
        buf = BytesIO()
        df.write_parquet(buf)
        buf.seek(0)
        mock_s3.get_object.return_value = {'Body': MagicMock(read=lambda: buf.getvalue())}

        result = load_parquet_from_s3("bucket", prefix="data/")

        # Should have listed twice
        self.assertEqual(mock_s3.list_objects_v2.call_count, 2)
        # Should have fetched 2 files
        self.assertEqual(mock_s3.get_object.call_count, 2)
        # Result should be length 2 (1 row + 1 row)
        self.assertEqual(len(result), 2)

    @patch('boto3.client')
    def test_no_files_found(self, mock_boto):
        """Test error raised when no parquet files exist"""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        # Return empty contents
        mock_s3.list_objects_v2.return_value = {"Contents": []} # or just empty dict if key missing

        with self.assertRaises(FileNotFoundError):
            load_parquet_from_s3("bucket", prefix="empty/")
