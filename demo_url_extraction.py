#!/usr/bin/env python3
"""
Demo script to showcase the PDF URL extraction feature.
This creates a simple demo showing the complete workflow.
"""
import os
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from markdown_generator import MarkdownGenerator
from pdf_downloader import PDFDownloader
from pdf_text_extractor import PDFTextExtractor
from url_extractor import SourceCodeURLExtractor


def create_sample_pdf(filename: str, content: str):
    """Create a sample PDF with content."""
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    text_object = c.beginText(50, height - 50)
    text_object.setFont("Helvetica", 10)
    
    for line in content.split('\n'):
        text_object.textLine(line)
    
    c.drawText(text_object)
    c.save()


def main():
    """Run the demo."""
    print("=" * 70)
    print("PDF URL Extraction Feature Demo")
    print("=" * 70)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, 'demo_thesis.pdf')
    
    # Create sample PDF with source code URLs
    content = """
    Sample Thesis: Machine Learning for Climate Prediction
    
    Author: Dr. Alice Johnson
    
    Abstract:
    This thesis presents a novel approach to climate prediction using
    deep learning techniques. The complete source code for our models
    is available at https://github.com/alice-johnson/climate-ml
    
    We also developed supporting tools available at:
    - Data preprocessing: https://gitlab.com/alice-johnson/climate-data
    - Visualization tools: https://github.com/alice-johnson/viz-tools
    
    Our experiments are reproducible using the code repositories above.
    
    Additional resources:
    - Dataset: https://example.com/dataset
    - Documentation: https://docs.example.com
    """
    
    print("\n1. Creating sample PDF...")
    create_sample_pdf(pdf_path, content)
    print(f"   PDF created at: {pdf_path}")
    
    print("\n2. Extracting text from PDF...")
    extractor = PDFTextExtractor()
    text = extractor.extract_text(pdf_path)
    print(f"   Extracted {len(text)} characters of text")
    
    print("\n3. Finding source code URLs...")
    url_extractor = SourceCodeURLExtractor()
    urls = url_extractor.extract_source_code_urls(text)
    
    print(f"   Found {len(urls)} source code URL(s):")
    for url in urls:
        print(f"     - {url}")
    
    print("\n4. Generating markdown table...")
    publications = [
        {
            'author': 'Dr. Alice Johnson',
            'title': 'Machine Learning for Climate Prediction',
            'url': 'https://example.com/thesis.pdf',
            'summary': 'This thesis presents a novel approach to climate prediction using deep learning techniques.',
            'source_urls': url_extractor.format_urls_for_display(urls)
        }
    ]
    
    generator = MarkdownGenerator(include_source_urls=True)
    markdown = generator.generate_document(publications, "Demo Output")
    
    print("\n5. Generated Markdown Table:")
    print("-" * 70)
    print(markdown)
    print("-" * 70)
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    
    print("\n✓ Demo completed successfully!")
    print("\nTo use this feature in production:")
    print("  1. Set EXTRACT_SOURCE_URLS=true in your .env file")
    print("  2. Run: python main.py")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except ImportError as e:
        print(f"Error: {e}")
        print("\nPlease install required dependencies:")
        print("  pip install reportlab")
