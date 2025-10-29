"""
Unit tests for PDF processing and URL extraction functionality.
"""
import unittest
import os
import tempfile
from url_extractor import SourceCodeURLExtractor


class TestSourceCodeURLExtractor(unittest.TestCase):
    """Test cases for SourceCodeURLExtractor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = SourceCodeURLExtractor()
    
    def test_extract_github_urls(self):
        """Test extraction of GitHub URLs."""
        text = """
        This project is available at https://github.com/user/repo
        and also at https://github.com/another/project
        """
        urls = self.extractor.extract_source_code_urls(text)
        self.assertEqual(len(urls), 2)
        self.assertIn('https://github.com/user/repo', urls)
        self.assertIn('https://github.com/another/project', urls)
    
    def test_extract_gitlab_urls(self):
        """Test extraction of GitLab URLs."""
        text = "Source code: https://gitlab.com/user/project"
        urls = self.extractor.extract_source_code_urls(text)
        self.assertEqual(len(urls), 1)
        self.assertIn('https://gitlab.com/user/project', urls)
    
    def test_extract_mixed_platform_urls(self):
        """Test extraction of URLs from multiple platforms."""
        text = """
        GitHub: https://github.com/user/repo1
        GitLab: https://gitlab.com/user/repo2
        Bitbucket: https://bitbucket.org/user/repo3
        """
        urls = self.extractor.extract_source_code_urls(text)
        self.assertEqual(len(urls), 3)
    
    def test_no_urls_found(self):
        """Test when no source code URLs are present."""
        text = "This is just plain text with no URLs."
        urls = self.extractor.extract_source_code_urls(text)
        self.assertEqual(len(urls), 0)
    
    def test_ignore_non_source_urls(self):
        """Test that non-source code URLs are filtered out."""
        text = """
        Visit https://www.google.com for more info.
        Source: https://github.com/user/repo
        """
        urls = self.extractor.extract_source_code_urls(text)
        self.assertEqual(len(urls), 1)
        self.assertIn('https://github.com/user/repo', urls)
    
    def test_extract_urls_with_paths(self):
        """Test extraction of URLs with paths and query parameters."""
        text = "https://github.com/user/repo/tree/main/src"
        urls = self.extractor.extract_source_code_urls(text)
        self.assertEqual(len(urls), 1)
        self.assertIn('https://github.com/user/repo/tree/main/src', urls)
    
    def test_format_urls_for_display(self):
        """Test formatting URLs for markdown display."""
        urls = [
            'https://github.com/user/repo1',
            'https://gitlab.com/user/repo2'
        ]
        formatted = self.extractor.format_urls_for_display(urls)
        self.assertIn('[Github]', formatted)
        self.assertIn('[Gitlab]', formatted)
    
    def test_format_empty_urls(self):
        """Test formatting empty URL list."""
        formatted = self.extractor.format_urls_for_display([])
        self.assertEqual(formatted, "N/A")
    
    def test_format_many_urls(self):
        """Test formatting with more than max_display URLs."""
        urls = [f'https://github.com/user/repo{i}' for i in range(5)]
        formatted = self.extractor.format_urls_for_display(urls, max_display=3)
        self.assertIn('+2 more', formatted)
    
    def test_url_cleaning(self):
        """Test that URLs are cleaned of trailing punctuation."""
        text = "Check https://github.com/user/repo. and https://gitlab.com/user/project,"
        urls = self.extractor.extract_source_code_urls(text)
        self.assertIn('https://github.com/user/repo', urls)
        self.assertIn('https://gitlab.com/user/project', urls)
        # Should not include trailing punctuation
        for url in urls:
            self.assertNotIn('.', url.split('/')[-1])


if __name__ == '__main__':
    unittest.main()
