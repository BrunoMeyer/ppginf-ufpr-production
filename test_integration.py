"""
Integration test for the PDF URL extraction feature.
This test demonstrates the complete workflow.
"""
import os
import tempfile
import unittest
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from pdf_downloader import PDFDownloader
from pdf_text_extractor import PDFTextExtractor
from url_extractor import SourceCodeURLExtractor


def create_test_pdf(text_content: str, filename: str):
    """
    Create a simple test PDF with text content.
    
    Args:
        text_content: Text to include in the PDF
        filename: Path to save the PDF
    """
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Add text to PDF
    text_object = c.beginText(50, height - 50)
    text_object.setFont("Helvetica", 12)
    
    # Split text into lines and add to PDF
    for line in text_content.split('\n'):
        text_object.textLine(line)
    
    c.drawText(text_object)
    c.save()


class TestIntegration(unittest.TestCase):
    """Integration tests for PDF processing and URL extraction."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.pdf_path = os.path.join(self.temp_dir, 'test_thesis.pdf')
        
        # Create a test PDF with source code URLs
        test_content = """
        Thesis: Advanced Machine Learning Techniques
        
        Author: John Doe
        
        Abstract:
        This thesis presents novel approaches to machine learning.
        The implementation is available at https://github.com/johndoe/ml-research
        
        Additional code repositories:
        - Data preprocessing: https://gitlab.com/johndoe/data-tools
        - Experiments: https://github.com/johndoe/experiments
        
        For more information, visit the project website.
        """
        
        create_test_pdf(test_content, self.pdf_path)
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_full_workflow(self):
        """Test the complete workflow: PDF creation -> text extraction -> URL extraction."""
        # Extract text from PDF
        text_extractor = PDFTextExtractor()
        text = text_extractor.extract_text(self.pdf_path)
        
        # Verify text was extracted
        self.assertIsNotNone(text)
        self.assertIn('Machine Learning', text)
        
        # Extract source code URLs
        url_extractor = SourceCodeURLExtractor()
        urls = url_extractor.extract_source_code_urls(text)
        
        # Verify URLs were found
        self.assertGreater(len(urls), 0)
        self.assertTrue(any('github.com/johndoe/ml-research' in url for url in urls))
        self.assertTrue(any('gitlab.com/johndoe/data-tools' in url for url in urls))
        
        # Format URLs for display
        formatted = url_extractor.format_urls_for_display(urls)
        self.assertIn('[Github]', formatted)
        self.assertIn('[Gitlab]', formatted)


if __name__ == '__main__':
    # Check if reportlab is available
    try:
        import reportlab
        unittest.main()
    except ImportError:
        print("Skipping integration tests: reportlab not installed")
        print("To run integration tests: pip install reportlab")
