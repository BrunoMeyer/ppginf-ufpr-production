"""
PDF text extraction module for extracting text from PDF files.
"""
from typing import Optional
import os


class PDFTextExtractor:
    """Extracts text from PDF files."""
    
    def __init__(self):
        """Initialize PDF text extractor."""
        self.pypdf_available = False
        self.pdfplumber_available = False
        
        # Try to import PDF libraries
        try:
            import PyPDF2
            self.pypdf_available = True
            self.PyPDF2 = PyPDF2
        except ImportError:
            pass
        
        try:
            import pdfplumber
            self.pdfplumber_available = True
            self.pdfplumber = pdfplumber
        except ImportError:
            pass
        
        if not self.pypdf_available and not self.pdfplumber_available:
            raise ImportError(
                "No PDF library available. Install PyPDF2 or pdfplumber: "
                "pip install PyPDF2 pdfplumber"
            )
    
    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """
        Extract text using PyPDF2.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = self.PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"  Error extracting text with PyPDF2: {e}")
        
        return text
    
    def extract_text_pdfplumber(self, pdf_path: str) -> str:
        """
        Extract text using pdfplumber.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        text = ""
        try:
            with self.pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"  Error extracting text with pdfplumber: {e}")
        
        return text
    
    def extract_text(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text, or None if extraction failed
        """
        if not os.path.exists(pdf_path):
            print(f"  PDF file not found: {pdf_path}")
            return None
        
        print(f"  Extracting text from: {os.path.basename(pdf_path)}")
        
        # Try pdfplumber first (generally better text extraction)
        if self.pdfplumber_available:
            text = self.extract_text_pdfplumber(pdf_path)
            if text.strip():
                return text
        
        # Fall back to PyPDF2
        if self.pypdf_available:
            text = self.extract_text_pypdf2(pdf_path)
            if text.strip():
                return text
        
        print(f"  Warning: No text extracted from PDF")
        return None
