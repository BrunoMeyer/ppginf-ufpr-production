"""
PDF downloader module for downloading thesis/dissertation PDFs.
"""
import os
import requests
from typing import Optional
from urllib.parse import urlparse


class PDFDownloader:
    """Downloads PDF files from URLs."""
    
    def __init__(self, download_dir: str = './downloads'):
        """
        Initialize PDF downloader.
        
        Args:
            download_dir: Directory to save downloaded PDFs
        """
        self.download_dir = download_dir
        self._ensure_download_dir()
    
    def _ensure_download_dir(self):
        """Create download directory if it doesn't exist."""
        os.makedirs(self.download_dir, exist_ok=True)
    
    def _get_filename_from_url(self, url: str) -> str:
        """
        Extract filename from URL or generate one.
        
        Args:
            url: URL to extract filename from
            
        Returns:
            Filename for the PDF
        """
        # Parse URL to get path
        parsed = urlparse(url)
        path = parsed.path
        
        # Get last component of path
        filename = os.path.basename(path)
        
        # If no filename or doesn't end with .pdf, generate one
        if not filename or not filename.lower().endswith('.pdf'):
            # Use UUID from path if available
            parts = path.split('/')
            if len(parts) > 2 and len(parts[-2]) > 20:
                filename = f"{parts[-2]}.pdf"
            else:
                filename = f"document_{hash(url) % 1000000}.pdf"
        
        return filename
    
    def download_pdf(self, url: str, timeout: int = 30) -> Optional[str]:
        """
        Download a PDF from URL.
        
        Args:
            url: URL of the PDF to download
            timeout: Request timeout in seconds
            
        Returns:
            Path to downloaded file, or None if download failed
        """
        if not url:
            return None
        
        try:
            # Generate filename
            filename = self._get_filename_from_url(url)
            filepath = os.path.join(self.download_dir, filename)
            
            # Skip if already downloaded
            if os.path.exists(filepath):
                print(f"  PDF already downloaded: {filename}")
                return filepath
            
            # Download PDF
            print(f"  Downloading: {url}")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'octet-stream' not in content_type:
                print(f"  Warning: URL may not be a PDF (content-type: {content_type})")
            
            # Save to file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"  Downloaded to: {filepath}")
            return filepath
            
        except requests.exceptions.RequestException as e:
            print(f"  Error downloading PDF from {url}: {e}")
            return None
        except Exception as e:
            print(f"  Unexpected error downloading PDF: {e}")
            return None
