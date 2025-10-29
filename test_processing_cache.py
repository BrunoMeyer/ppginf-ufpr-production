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


if __name__ == '__main__':
    unittest.main()
