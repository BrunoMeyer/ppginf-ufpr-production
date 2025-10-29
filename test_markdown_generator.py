"""
Unit tests for the DSpace extraction project.
"""
import unittest
from markdown_generator import MarkdownGenerator


class TestMarkdownGenerator(unittest.TestCase):
    """Test cases for MarkdownGenerator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = MarkdownGenerator()
        
    def test_escape_markdown(self):
        """Test markdown escaping."""
        text = "This has | pipes and\nnewlines"
        escaped = self.generator.escape_markdown(text)
        self.assertNotIn('|', escaped.replace('\\|', ''))
        self.assertNotIn('\n', escaped)
        
    def test_truncate_text(self):
        """Test text truncation."""
        long_text = "a" * 250
        truncated = self.generator.truncate_text(long_text, 200)
        self.assertEqual(len(truncated), 200)
        self.assertTrue(truncated.endswith('...'))
        
    def test_generate_table(self):
        """Test table generation."""
        publications = [
            {
                'author': 'John Doe',
                'title': 'Test Thesis',
                'url': 'http://example.com/doc.pdf',
                'summary': 'This is a test summary'
            },
            {
                'author': 'Jane Smith',
                'title': 'Another Work',
                'url': 'http://example.com/doc2.pdf',
                'summary': 'Another summary'
            }
        ]
        
        table = self.generator.generate_table(publications)
        
        # Check header
        self.assertIn('Author', table)
        self.assertIn('Title', table)
        self.assertIn('URL', table)
        self.assertIn('Summary', table)
        
        # Check data
        self.assertIn('John Doe', table)
        self.assertIn('Test Thesis', table)
        self.assertIn('[Link](http://example.com/doc.pdf)', table)
        
    def test_generate_document(self):
        """Test complete document generation."""
        publications = [
            {
                'author': 'Test Author',
                'title': 'Test Title',
                'url': 'http://test.com',
                'summary': 'Test summary'
            }
        ]
        
        doc = self.generator.generate_document(publications, "Test Document")
        
        # Check document structure
        self.assertIn('# Test Document', doc)
        self.assertIn('Total publications: 1', doc)
        self.assertIn('Test Author', doc)
    
    def test_generate_document_with_ollama_analysis(self):
        """Test document generation with Ollama analysis."""
        generator = MarkdownGenerator(include_ollama_analysis=True)
        publications = [
            {
                'author': 'Test Author',
                'title': 'Test Title',
                'url': 'http://test.com',
                'summary': 'Test summary',
                'ollama_analysis': '# Analysis\n\nThis is a test analysis.'
            }
        ]
        
        doc = generator.generate_document(publications, "Test Document")
        
        # Check document structure
        self.assertIn('# Test Document', doc)
        self.assertIn('Document Analyses', doc)
        self.assertIn('Document 1: Test Title', doc)
        self.assertIn('**Author:** Test Author', doc)
        self.assertIn('This is a test analysis.', doc)


if __name__ == '__main__':
    unittest.main()
