"""
PDF text extraction module for extracting text from PDF files.
"""
from typing import Optional
import os
import multiprocessing
import time


class PDFTextExtractor:
    """Extracts text from PDF files."""
    
    def __init__(self):
        """Initialize PDF text extractor."""
        self.pypdf_available = False
        self.pdfplumber_available = False
        self.use_pypdf2 = False
        
        # Try to import PDF libraries
        try:
            import pypdf
            self.pypdf_available = True
            self.pypdf = pypdf
        except ImportError:
            # Fall back to PyPDF2 if pypdf is not available
            try:
                import PyPDF2
                self.pypdf_available = True
                self.PyPDF2 = PyPDF2
                self.use_pypdf2 = True
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
                "No PDF library available. Install pypdf or pdfplumber: "
                "pip install pypdf pdfplumber"
            )
    
    def extract_text_pypdf(self, pdf_path: str) -> str:
        """
        Extract text using pypdf or PyPDF2.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                # Use pypdf if available, otherwise PyPDF2
                if self.use_pypdf2:
                    reader = self.PyPDF2.PdfReader(file)
                else:
                    reader = self.pypdf.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"  Error extracting text with pypdf: {e}")
        
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
        
        return self.extract_text_with_timeout(pdf_path)

    def extract_text_with_timeout(self, pdf_path: str, timeout: int = 30) -> Optional[str]:
        """
        Extract text from a PDF file using a separate process and a timeout.

        Args:
            pdf_path: Path to PDF file
            timeout: Seconds to wait for extraction before terminating the worker

        Returns:
            Extracted text, or None if extraction failed or timed out
        """
        print(f"  Extracting text from: {os.path.basename(pdf_path)} (timeout={timeout}s)")

        # Use a separate process to avoid blocking/hangs inside C extensions
        result_q = multiprocessing.Queue()
        worker = multiprocessing.Process(target=_extract_text_worker, args=(pdf_path, result_q))
        worker.start()
        worker.join(timeout)

        if worker.is_alive():
            # Timed out, terminate the worker
            try:
                worker.terminate()
            except Exception:
                pass
            worker.join(1)
            print(f"  Timeout ({timeout}s) extracting text from: {os.path.basename(pdf_path)}")
            return None

        # Worker finished — try to get result
        text = None
        try:
            result = result_q.get_nowait()
            if isinstance(result, dict):
                if 'error' in result and result['error']:
                    print(f"  Extraction error: {result['error']}")
                text = result.get('text')
            else:
                # Old-style string result
                text = result
        except Exception:
            # No result or queue empty
            text = None

        if text and str(text).strip():
            return text

        print(f"  Warning: No text extracted from PDF")
        return None


def _extract_text_worker(pdf_path: str, result_queue: "multiprocessing.Queue") -> None:
    """Worker function run in a separate process to extract text and put result in the queue.

    We import pdf libraries inside the worker to avoid relying on pickling module objects.
    The worker will try pdfplumber first, then pypdf / PyPDF2.
    On error it will put {'error': str(e), 'text': text_so_far} into the queue.
    """
    text = ""
    try:
        # Try pdfplumber first
        try:
            import pdfplumber
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        try:
                            page_text = page.extract_text()
                        except Exception:
                            page_text = None
                        if page_text:
                            text += page_text + "\n"
                if text.strip():
                    result_queue.put({'text': text})
                    return
            except Exception as e:
                # Log but proceed to try pypdf
                result_queue.put({'error': f'pdfplumber error: {e}', 'text': text})
        except ImportError:
            pass

        # Try pypdf or PyPDF2
        try:
            try:
                import pypdf as pypdf
                use_pypdf2 = False
            except ImportError:
                import PyPDF2 as PyPDF2
                pypdf = None
                use_pypdf2 = True

            with open(pdf_path, 'rb') as f:
                if use_pypdf2:
                    reader = PyPDF2.PdfReader(f)
                else:
                    reader = pypdf.PdfReader(f)

                for page in reader.pages:
                    try:
                        page_text = page.extract_text()
                    except Exception:
                        page_text = None
                    if page_text:
                        text += page_text + "\n"

            result_queue.put({'text': text})
            return
        except ImportError:
            # No pypdf / PyPDF2 available
            result_queue.put({'error': 'No PDF library available in worker', 'text': text})
            return
        except Exception as e:
            result_queue.put({'error': f'pypdf error: {e}', 'text': text})
            return

    except Exception as e:
        # Catch-all to ensure some result is put
        try:
            result_queue.put({'error': f'unknown worker error: {e}', 'text': text})
        except Exception:
            pass
