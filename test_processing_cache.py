"""
Unit tests for processing cache functionality.
"""
import unittest
import os
import tempfile
import shutil
from processing_cache import ProcessingCache


class TestProcessingCache(unittest.TestCase):
    """Test cases for ProcessingCache."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = ProcessingCache(cache_dir=self.temp_dir)
        self.test_pdf = os.path.join(self.temp_dir, 'test.pdf')
        
        # Create a dummy PDF file
        with open(self.test_pdf, 'w') as f:
            f.write('dummy pdf content')
    
    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cache_and_retrieve_urls(self):
        """Test caching and retrieving URLs."""
        urls = ['https://github.com/user/repo1', 'https://gitlab.com/user/repo2']
        
        # Cache URLs
        self.cache.cache_urls(self.test_pdf, urls)
        
        # Retrieve cached URLs
        cached = self.cache.get_cached_urls(self.test_pdf)
        self.assertEqual(cached, urls)
    
    def test_cache_empty_urls(self):
        """Test caching empty URL list."""
        self.cache.cache_urls(self.test_pdf, [])
        cached = self.cache.get_cached_urls(self.test_pdf)
        self.assertEqual(cached, [])
    
    def test_no_cache_for_nonexistent_file(self):
        """Test that nonexistent file returns None."""
        nonexistent = os.path.join(self.temp_dir, 'nonexistent.pdf')
        cached = self.cache.get_cached_urls(nonexistent)
        self.assertIsNone(cached)
    
    def test_cache_invalidates_on_file_modification(self):
        """Test that cache is invalidated when file is modified."""
        urls1 = ['https://github.com/user/repo1']
        self.cache.cache_urls(self.test_pdf, urls1)
        
        # Modify the file
        import time
        time.sleep(0.01)  # Ensure modification time changes
        with open(self.test_pdf, 'a') as f:
            f.write('more content')
        
        # Cache should not return old URLs
        cached = self.cache.get_cached_urls(self.test_pdf)
        self.assertIsNone(cached)
        
        # Cache new URLs
        urls2 = ['https://github.com/user/repo2']
        self.cache.cache_urls(self.test_pdf, urls2)
        
        # Should get new URLs
        cached = self.cache.get_cached_urls(self.test_pdf)
        self.assertEqual(cached, urls2)
    
    def test_cache_persistence(self):
        """Test that cache persists across instances."""
        urls = ['https://github.com/user/repo']
        self.cache.cache_urls(self.test_pdf, urls)
        
        # Create new cache instance
        new_cache = ProcessingCache(cache_dir=self.temp_dir)
        cached = new_cache.get_cached_urls(self.test_pdf)
        self.assertEqual(cached, urls)
    
    def test_clear_cache(self):
        """Test clearing cache."""
        urls = ['https://github.com/user/repo']
        self.cache.cache_urls(self.test_pdf, urls)
        
        # Clear cache
        self.cache.clear_cache()
        
        # Should not find cached URLs
        cached = self.cache.get_cached_urls(self.test_pdf)
        self.assertIsNone(cached)
    
    def test_cache_dspace_response(self):
        """Test caching DSpace HTTP response."""
        url = 'https://dspace.example.org/rest/collections/123/items'
        response_body = {
            'items': [
                {'id': '1', 'metadata': [{'key': 'dc.title', 'value': 'Test Thesis'}]},
                {'id': '2', 'metadata': [{'key': 'dc.title', 'value': 'Another Thesis'}]}
            ]
        }
        resolved_url = 'https://dspace.example.org/rest/collections/123/items'
        
        # Cache the response
        self.cache.cache_dspace_response(url, response_body, resolved_url)
        
        # Retrieve cached response
        cached = self.cache.get_cached_dspace_response(url)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['response_body'], response_body)
        self.assertEqual(cached['resolved_url'], resolved_url)
    
    def test_cache_dspace_response_with_redirect(self):
        """Test caching DSpace HTTP response with redirect URL."""
        url = 'https://dspace.example.org/rest/collections/123/items'
        response_body = {'items': []}
        # Simulate a redirect to a different URL
        resolved_url = 'https://dspace-prod.example.org/rest/collections/123/items'
        
        # Cache the response
        self.cache.cache_dspace_response(url, response_body, resolved_url)
        
        # Retrieve cached response
        cached = self.cache.get_cached_dspace_response(url)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['resolved_url'], resolved_url)
    
    def test_get_cached_dspace_response_not_found(self):
        """Test retrieving non-existent DSpace response returns None."""
        url = 'https://dspace.example.org/rest/collections/nonexistent/items'
        cached = self.cache.get_cached_dspace_response(url)
        self.assertIsNone(cached)
    
    def test_cache_dspace_response_persistence(self):
        """Test that DSpace response cache persists across instances."""
        url = 'https://dspace.example.org/rest/collections/456/items'
        response_body = {'items': [{'id': '1'}]}
        resolved_url = 'https://dspace.example.org/rest/collections/456/items'
        
        # Cache the response
        self.cache.cache_dspace_response(url, response_body, resolved_url)
        
        # Create new cache instance
        new_cache = ProcessingCache(cache_dir=self.temp_dir)
        cached = new_cache.get_cached_dspace_response(url)
        
        self.assertIsNotNone(cached)
        self.assertEqual(cached['response_body'], response_body)
        self.assertEqual(cached['resolved_url'], resolved_url)
    
    def test_backward_compatibility_old_cache_entries(self):
        """Test backward compatibility with old cache entries that lack new fields."""
        # Simulate an old cache entry (just a URL list, not a dict with response_body)
        url = 'https://dspace.example.org/old/endpoint'
        self.cache.cache[f"dspace_response:{url}"] = ['old', 'style', 'entry']
        self.cache._save_cache()
        
        # Should return None for old-style entries
        cached = self.cache.get_cached_dspace_response(url)
        self.assertIsNone(cached)


if __name__ == '__main__':
    unittest.main()
