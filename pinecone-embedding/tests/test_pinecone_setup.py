import unittest
from unittest.mock import patch, MagicMock
import os
from rag_ingest.pinecone_setup import init_pinecone

class TestPineconeSetup(unittest.TestCase):

    @patch.dict(os.environ, {"PINECONE_API_KEY": "fake-key"})
    @patch("rag_ingest.pinecone_setup.Pinecone")
    def test_init_creates_index_if_missing(self, mock_cls):
        """Test that create_index is called when has_index returns False"""
        mock_pc = MagicMock()
        mock_cls.return_value = mock_pc
        
        # Simulate index missing
        mock_pc.has_index.return_value = False
        
        init_pinecone("new-index")
        
        mock_pc.create_index.assert_called_once()
        mock_pc.Index.assert_called_with("new-index")

    @patch.dict(os.environ, {"PINECONE_API_KEY": "fake-key"})
    @patch("rag_ingest.pinecone_setup.Pinecone")
    def test_init_skips_creation_if_exists(self, mock_cls):
        """Test that create_index is NOT called when has_index returns True"""
        mock_pc = MagicMock()
        mock_cls.return_value = mock_pc
        
        # Simulate index exists
        mock_pc.has_index.return_value = True
        
        init_pinecone("existing-index")
        
        mock_pc.create_index.assert_not_called()
        mock_pc.Index.assert_called_with("existing-index")

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key_raises_error(self):
        """Test that ValueError is raised if env var is missing"""
        with self.assertRaises(ValueError):
            init_pinecone("test")
