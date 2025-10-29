"""
Tests for the Ollama analyzer module.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from ollama_analyzer import OllamaAnalyzer


class TestOllamaAnalyzer(unittest.TestCase):
    """Test cases for OllamaAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.endpoint = "http://localhost:11434"
        self.model = "llama2"
        self.analyzer = OllamaAnalyzer(self.endpoint, self.model)
    
    def test_initialization(self):
        """Test analyzer initialization."""
        self.assertEqual(self.analyzer.endpoint, self.endpoint)
        self.assertEqual(self.analyzer.model, self.model)
        self.assertIsNotNone(self.analyzer.session)
    
    def test_endpoint_trailing_slash_removal(self):
        """Test that trailing slashes are removed from endpoint."""
        analyzer = OllamaAnalyzer("http://localhost:11434/", "llama2")
        self.assertEqual(analyzer.endpoint, "http://localhost:11434")
    
    @patch('ollama_analyzer.requests.Session.post')
    def test_call_ollama_success(self, mock_post):
        """Test successful Ollama API call."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {'response': 'Test analysis result'}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = self.analyzer._call_ollama("Test prompt")
        
        self.assertEqual(result, 'Test analysis result')
        mock_post.assert_called_once()
        
        # Verify the call parameters
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], f"{self.endpoint}/api/generate")
        self.assertEqual(call_args[1]['json']['model'], self.model)
        self.assertEqual(call_args[1]['json']['prompt'], "Test prompt")
        self.assertFalse(call_args[1]['json']['stream'])
    
    @patch('ollama_analyzer.requests.Session.post')
    def test_call_ollama_request_error(self, mock_post):
        """Test Ollama API call with request error."""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        result = self.analyzer._call_ollama("Test prompt")
        
        self.assertIsNone(result)
    
    @patch('ollama_analyzer.requests.Session.post')
    def test_call_ollama_json_error(self, mock_post):
        """Test Ollama API call with JSON parsing error."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = self.analyzer._call_ollama("Test prompt")
        
        self.assertIsNone(result)
    
    @patch.object(OllamaAnalyzer, '_call_ollama')
    def test_analyze_document_success(self, mock_call_ollama):
        """Test successful document analysis."""
        mock_call_ollama.return_value = "# Document Analysis\n\n## Main Points\nTest analysis"
        
        text = "This is a test document about machine learning."
        result = self.analyzer.analyze_document(text)
        
        self.assertIsNotNone(result)
        self.assertIn("Document Analysis", result)
        mock_call_ollama.assert_called_once()
    
    @patch.object(OllamaAnalyzer, '_call_ollama')
    def test_analyze_document_empty_text(self, mock_call_ollama):
        """Test document analysis with empty text."""
        result = self.analyzer.analyze_document("")
        
        self.assertIsNone(result)
        mock_call_ollama.assert_not_called()
    
    @patch.object(OllamaAnalyzer, '_call_ollama')
    def test_analyze_document_whitespace_only(self, mock_call_ollama):
        """Test document analysis with whitespace-only text."""
        result = self.analyzer.analyze_document("   \n\t  ")
        
        self.assertIsNone(result)
        mock_call_ollama.assert_not_called()
    
    @patch.object(OllamaAnalyzer, '_call_ollama')
    def test_analyze_document_failed_analysis(self, mock_call_ollama):
        """Test document analysis when API call fails."""
        mock_call_ollama.return_value = None
        
        text = "This is a test document."
        result = self.analyzer.analyze_document(text)
        
        self.assertIsNone(result)
    
    @patch.object(OllamaAnalyzer, '_call_ollama')
    def test_analyze_document_truncation(self, mock_call_ollama):
        """Test that very long documents are truncated."""
        mock_call_ollama.return_value = "Analysis result"
        
        # Create a very long document
        long_text = "word " * 100000  # Much longer than 50000 chars
        result = self.analyzer.analyze_document(long_text)
        
        # Check that the prompt sent to Ollama contains truncated text
        call_args = mock_call_ollama.call_args[0][0]
        # The truncated text should be in the prompt
        self.assertTrue(len(call_args) < len(long_text))
    
    @patch('ollama_analyzer.requests.Session.get')
    def test_connection_success(self, mock_get):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = self.analyzer.test_connection()
        
        self.assertTrue(result)
        mock_get.assert_called_once_with(f"{self.endpoint}/api/tags", timeout=5)
    
    @patch('ollama_analyzer.requests.Session.get')
    def test_connection_failure(self, mock_get):
        """Test connection test failure."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Cannot connect")
        
        result = self.analyzer.test_connection()
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
