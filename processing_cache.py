"""
Cache manager for storing processed PDF results and DSpace HTTP responses.
"""
import os
import json
from typing import List, Optional, Dict, Any


class ProcessingCache:
    """Manages cache of processed PDFs and their extracted URLs, as well as DSpace HTTP responses."""
    
    def __init__(self, cache_dir: str = './downloads'):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache file
        """
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, '.processing_cache.json')
        self.cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        """Load cache from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"  Warning: Could not load cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"  Warning: Could not save cache: {e}")
    
    def get_cached_urls(self, pdf_path: str) -> Optional[List[str]]:
        """
        Get cached URLs for a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of cached URLs, or None if not in cache
        """
        # Use file modification time as part of cache key
        if not os.path.exists(pdf_path):
            return None
        
        mtime = os.path.getmtime(pdf_path)
        cache_key = f"{pdf_path}:{mtime}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        return None
    
    def cache_urls(self, pdf_path: str, urls: List[str]):
        """
        Cache extracted URLs for a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            urls: List of URLs extracted from the PDF
        """
        if not os.path.exists(pdf_path):
            return
        
        mtime = os.path.getmtime(pdf_path)
        cache_key = f"{pdf_path}:{mtime}"
        
        self.cache[cache_key] = urls
        self._save_cache()
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache = {}
        self._save_cache()
    
    def get_cached_dspace_response(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached DSpace HTTP response for a URL.
        
        Args:
            url: The request URL
            
        Returns:
            Dictionary with 'response_body' and 'resolved_url', or None if not in cache
        """
        cache_key = f"dspace_response:{url}"
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            # Ensure backward compatibility - old cache entries may not have these fields
            if isinstance(cached_data, dict) and 'response_body' in cached_data:
                return cached_data
        
        return None
    
    def cache_dspace_response(self, url: str, response_body: Any, resolved_url: str):
        """
        Cache DSpace HTTP response body and resolved URL.
        
        Args:
            url: The request URL
            response_body: The HTTP response body (will be JSON serialized)
            resolved_url: The final/resolved URL (e.g., after redirects)
        """
        cache_key = f"dspace_response:{url}"
        
        self.cache[cache_key] = {
            'response_body': response_body,
            'resolved_url': resolved_url
        }
        self._save_cache()
