"""
Unit tests for DSpace client with caching functionality.
"""
import unittest
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from dspace_client import DSpaceClient
from processing_cache import ProcessingCache


class TestDSpaceClientCaching(unittest.TestCase):
    """Test cases for DSpaceClient caching."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = ProcessingCache(cache_dir=self.temp_dir)
        self.endpoint = 'https://dspace.example.org'
    
    def tearDown(self):
        """Clean up test files."""
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
    
    @patch('dspace_client.requests.Session')
    def test_cache_disabled_by_default(self, mock_session):
        """Test that caching is disabled when no cache is provided."""
        # Create client without cache
        client = DSpaceClient(self.endpoint)
        
        # Verify cache is None
        self.assertIsNone(client.cache)
    
    @patch('dspace_client.requests.Session')
    def test_cache_enabled_when_provided(self, mock_session):
        """Test that caching is enabled when cache is provided."""
        # Create client with cache
        client = DSpaceClient(self.endpoint, cache=self.cache)
        
        # Verify cache is set
        self.assertIsNotNone(client.cache)
        self.assertEqual(client.cache, self.cache)
    
    @patch('dspace_client.requests.Session')
    def test_http_response_cached(self, mock_session):
        """Test that HTTP responses are cached."""
        # Create mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = 'https://dspace.example.org/rest/communities/123/collections'
        mock_response.json.return_value = [
            {'uuid': 'col1', 'name': 'Collection 1'},
            {'uuid': 'col2', 'name': 'Collection 2'}
        ]
        
        # Set up mock session
        mock_session_instance = mock_session.return_value
        mock_session_instance.get.return_value = mock_response
        
        # Create client with cache
        client = DSpaceClient(self.endpoint, cache=self.cache)
        
        # Make a request
        url = f"{self.endpoint}/rest/communities/123/collections"
        response = client._get_with_cache(url, headers={})
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Verify response was cached
        cached = self.cache.get_cached_dspace_response(url)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['response_body'], mock_response.json.return_value)
        self.assertEqual(cached['resolved_url'], mock_response.url)
    
    @patch('dspace_client.requests.Session')
    def test_cached_response_used_on_second_call(self, mock_session):
        """Test that cached response is used on subsequent calls."""
        # Create mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = 'https://dspace.example.org/rest/communities/123/collections'
        mock_response.json.return_value = [{'uuid': 'col1'}]
        
        # Set up mock session
        mock_session_instance = mock_session.return_value
        mock_session_instance.get.return_value = mock_response
        
        # Create client with cache
        client = DSpaceClient(self.endpoint, cache=self.cache)
        
        # Make first request
        url = f"{self.endpoint}/rest/communities/123/collections"
        response1 = client._get_with_cache(url, headers={})
        self.assertEqual(response1.json(), [{'uuid': 'col1'}])
        
        # Verify session.get was called once
        self.assertEqual(mock_session_instance.get.call_count, 1)
        
        # Make second request - should use cache
        response2 = client._get_with_cache(url, headers={})
        self.assertEqual(response2.json(), [{'uuid': 'col1'}])
        
        # Verify session.get was NOT called again (still 1 time)
        self.assertEqual(mock_session_instance.get.call_count, 1)
    
    @patch('dspace_client.requests.Session')
    def test_resolved_url_stored_for_redirects(self, mock_session):
        """Test that resolved URL is stored when redirects occur."""
        # Create mock response with redirect
        mock_response = Mock()
        mock_response.status_code = 200
        # Original URL
        original_url = 'https://dspace.example.org/rest/communities/123/collections'
        # Resolved URL after redirect
        mock_response.url = 'https://dspace-prod.example.org/rest/communities/123/collections'
        mock_response.json.return_value = [{'uuid': 'col1'}]
        
        # Set up mock session
        mock_session_instance = mock_session.return_value
        mock_session_instance.get.return_value = mock_response
        
        # Create client with cache
        client = DSpaceClient(self.endpoint, cache=self.cache)
        
        # Make request
        response = client._get_with_cache(original_url, headers={})
        
        # Verify resolved URL was cached
        cached = self.cache.get_cached_dspace_response(original_url)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['resolved_url'], mock_response.url)
        self.assertNotEqual(cached['resolved_url'], original_url)
    
    @patch('dspace_client.requests.Session')
    def test_caching_preserves_metadata(self, mock_session):
        """Test that caching preserves all metadata in response."""
        # Create mock response with complex metadata
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = 'https://dspace.example.org/rest/collections/col1/items'
        mock_response.json.return_value = [
            {
                'id': 'item1',
                'metadata': [
                    {'key': 'dc.contributor.author', 'value': 'John Doe'},
                    {'key': 'dc.title', 'value': 'Test Thesis'},
                    {'key': 'dc.description.abstract', 'value': 'This is a test abstract'}
                ],
                'bitstreams': [
                    {'name': 'thesis.pdf', 'retrieveLink': '/bitstreams/123/retrieve'}
                ]
            }
        ]
        
        # Set up mock session
        mock_session_instance = mock_session.return_value
        mock_session_instance.get.return_value = mock_response
        
        # Create client with cache
        client = DSpaceClient(self.endpoint, cache=self.cache)
        
        # Make request
        url = f"{self.endpoint}/rest/collections/col1/items"
        response1 = client._get_with_cache(url, params={'expand': 'metadata,bitstreams'})
        data1 = response1.json()
        
        # Make second request (should use cache)
        response2 = client._get_with_cache(url, params={'expand': 'metadata,bitstreams'})
        data2 = response2.json()
        
        # Verify both responses have the same metadata
        self.assertEqual(data1, data2)
        self.assertEqual(data2[0]['metadata'][0]['value'], 'John Doe')
        self.assertEqual(data2[0]['metadata'][1]['value'], 'Test Thesis')


if __name__ == '__main__':
    unittest.main()
