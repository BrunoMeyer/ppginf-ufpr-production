"""
Tests for the production output module.
"""
import unittest
import os
import json
import shutil
import tempfile
from production_output import ProductionOutput


class TestProductionOutput(unittest.TestCase):
    """Test cases for ProductionOutput class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        self.output = ProductionOutput(self.test_dir)
        
        # Sample publication data
        self.sample_pub = {
            'title': 'Test Document Title',
            'author': 'John Doe',
            'url': 'https://example.com/doc.pdf',
            'summary': 'This is a test summary.',
            'source_urls': '[Github](https://github.com/test/repo)',
            'ollama_analysis': '# Analysis\n\nThis is a test analysis.'
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove the temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test output manager initialization."""
        self.assertEqual(self.output.output_dir, self.test_dir)
        self.assertTrue(os.path.exists(self.test_dir))
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test with invalid characters
        result = self.output._sanitize_filename('test<>:"/\\|?*file')
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)
        self.assertNotIn(':', result)
        
        # Test with long filename
        long_name = 'a' * 100
        result = self.output._sanitize_filename(long_name, max_length=50)
        self.assertEqual(len(result), 50)
        
        # Test with empty string
        result = self.output._sanitize_filename('')
        self.assertEqual(result, 'untitled')
    
    def test_generate_doc_id(self):
        """Test document ID generation."""
        doc_id = self.output._generate_doc_id(self.sample_pub)
        self.assertIsInstance(doc_id, str)
        self.assertEqual(len(doc_id), 12)
        
        # Same publication should generate same ID
        doc_id2 = self.output._generate_doc_id(self.sample_pub)
        self.assertEqual(doc_id, doc_id2)
        
        # Different publication should generate different ID
        different_pub = self.sample_pub.copy()
        different_pub['title'] = 'Different Title'
        doc_id3 = self.output._generate_doc_id(different_pub)
        self.assertNotEqual(doc_id, doc_id3)
    
    def test_extract_embedding_from_analysis(self):
        """Test embedding extraction."""
        analysis = "This is a research paper about methods and results."
        embedding = self.output._extract_embedding_from_analysis(analysis)
        
        self.assertIsNotNone(embedding)
        self.assertIsInstance(embedding, list)
        self.assertTrue(len(embedding) > 0)
        self.assertTrue(all(isinstance(x, (int, float)) for x in embedding))
        
        # Test with empty analysis
        embedding = self.output._extract_embedding_from_analysis('')
        self.assertIsNone(embedding)
        
        # Test with 'Analysis not available'
        embedding = self.output._extract_embedding_from_analysis('Analysis not available')
        self.assertIsNone(embedding)
    
    def test_save_document_summary(self):
        """Test saving document summary."""
        filepath = self.output.save_document_summary(self.sample_pub, 1)
        
        # Check that file was created
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('_summary.md'))
        
        # Check file contents
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('Test Document Title', content)
        self.assertIn('John Doe', content)
        self.assertIn('This is a test summary', content)
        self.assertIn('This is a test analysis', content)
    
    def test_save_document_vector(self):
        """Test saving document vector."""
        extracted_text = "This is the full extracted text from the document."
        filepath = self.output.save_document_vector(
            self.sample_pub, 
            1, 
            extracted_text, 
            'llama2'
        )
        
        # Check that file was created
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('_vector.json'))
        
        # Check file contents
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check structure
        self.assertIn('document_id', data)
        self.assertIn('index', data)
        self.assertIn('metadata', data)
        self.assertIn('text_data', data)
        self.assertIn('vector', data)
        
        # Check metadata
        self.assertEqual(data['metadata']['title'], 'Test Document Title')
        self.assertEqual(data['metadata']['author'], 'John Doe')
        self.assertEqual(data['metadata']['ollama_model'], 'llama2')
        
        # Check text data
        self.assertEqual(data['text_data']['total_characters'], len(extracted_text))
        self.assertIn('extracted_text', data['text_data'])
        
        # Check vector
        self.assertIn('embedding', data['vector'])
        self.assertIsInstance(data['vector']['embedding'], list)
    
    def test_save_all_documents(self):
        """Test saving all documents."""
        publications = [
            self.sample_pub,
            {
                'title': 'Second Document',
                'author': 'Jane Smith',
                'url': 'https://example.com/doc2.pdf',
                'summary': 'Second summary',
                'source_urls': 'N/A',
                'ollama_analysis': 'Second analysis'
            }
        ]
        
        extracted_texts = {
            'https://example.com/doc.pdf': 'First document text',
            'https://example.com/doc2.pdf': 'Second document text'
        }
        
        saved_files = self.output.save_all_documents(
            publications, 
            extracted_texts, 
            'llama2'
        )
        
        # Check that we got the right number of files
        self.assertEqual(len(saved_files['summaries']), 2)
        self.assertEqual(len(saved_files['vectors']), 2)
        
        # Check that all files exist
        for filepath in saved_files['summaries'] + saved_files['vectors']:
            self.assertTrue(os.path.exists(filepath))
    
    def test_save_document_with_special_characters(self):
        """Test saving document with special characters in title."""
        special_pub = {
            'title': 'Test: Document / With * Special <> Characters?',
            'author': 'Test Author',
            'url': 'https://example.com/special.pdf',
            'summary': 'Test summary',
            'source_urls': 'N/A',
            'ollama_analysis': 'Test analysis'
        }
        
        filepath = self.output.save_document_summary(special_pub, 1)
        
        # File should be created successfully
        self.assertTrue(os.path.exists(filepath))
        
        # Filename should not contain invalid characters
        filename = os.path.basename(filepath)
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            self.assertNotIn(char, filename)
    
    def test_save_document_without_ollama_analysis(self):
        """Test saving document without Ollama analysis."""
        pub_without_analysis = {
            'title': 'No Analysis Document',
            'author': 'Test Author',
            'url': 'https://example.com/noanalysis.pdf',
            'summary': 'Test summary',
            'source_urls': 'N/A'
        }
        
        # Should still save successfully
        summary_path = self.output.save_document_summary(pub_without_analysis, 1)
        vector_path = self.output.save_document_vector(pub_without_analysis, 1, '', 'llama2')
        
        self.assertTrue(os.path.exists(summary_path))
        self.assertTrue(os.path.exists(vector_path))
        
        # Check that vector has null embedding
        with open(vector_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIsNone(data['vector']['embedding'])


if __name__ == '__main__':
    unittest.main()
