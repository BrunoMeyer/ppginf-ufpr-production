"""
URL extraction module for finding source code repository URLs in text.
"""
import re
from typing import List, Set


class SourceCodeURLExtractor:
    """Extracts source code repository URLs from text."""
    
    # Common source code hosting platforms
    PLATFORMS = [
        'github.com',
        'gitlab.com',
        'bitbucket.org',
        'sourceforge.net',
        'codeberg.org',
        'gitea.io',
        'git.sr.ht',
    ]
    
    # Keywords that suggest a URL is related to source code
    SOURCE_CODE_KEYWORDS = [
        'repository', 'repo', 'source', 'code', 'git', 'svn',
        'implementation', 'software', 'program', 'project',
        'disponível', 'available', 'acesso', 'access'
    ]
    
    def __init__(self):
        """Initialize URL extractor."""
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for URL extraction."""
        # Pattern to match URLs
        self.url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            re.IGNORECASE
        )
        
        # Pattern to match platform-specific URLs
        platform_domains = '|'.join(re.escape(p) for p in self.PLATFORMS)
        self.platform_pattern = re.compile(
            rf'https?://(?:www\.)?(?:{platform_domains})/[^\s<>"{{}}|\\^`\[\]]+',
            re.IGNORECASE
        )
    
    def extract_urls(self, text: str) -> List[str]:
        """
        Extract all URLs from text.
        
        Args:
            text: Text to extract URLs from
            
        Returns:
            List of URLs found in text
        """
        if not text:
            return []
        
        urls = self.url_pattern.findall(text)
        
        # Clean up URLs (remove trailing punctuation)
        cleaned_urls = []
        for url in urls:
            # Remove trailing punctuation
            url = url.rstrip('.,;:!?)')
            # Remove trailing HTML tags
            url = re.sub(r'<[^>]+>$', '', url)
            if url:
                cleaned_urls.append(url)
        
        return cleaned_urls
    
    def extract_source_code_urls(self, text: str) -> List[str]:
        """
        Extract source code repository URLs from text.
        
        Args:
            text: Text to search for URLs
            
        Returns:
            List of unique source code URLs found
        """
        if not text:
            return []
        
        found_urls: Set[str] = set()
        
        # Extract all URLs
        all_urls = self.extract_urls(text)
        
        # Filter URLs by platform
        for url in all_urls:
            url_lower = url.lower()
            
            # Check if URL is from a known source code platform
            for platform in self.PLATFORMS:
                if platform in url_lower:
                    found_urls.add(url)
                    break
        
        # Also look for URLs in context with source code keywords
        # This helps catch repository URLs that might be on custom domains
        for keyword in self.SOURCE_CODE_KEYWORDS:
            # Look for keyword near URLs (within 100 characters)
            pattern = rf'.{{0,100}}{re.escape(keyword)}.{{0,100}}https?://[^\s<>"{{}}|\\^`\[\]]+'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract URL from the match
                url_matches = self.url_pattern.findall(match.group())
                for url in url_matches:
                    url = url.rstrip('.,;:!?)')
                    # Add if it looks like a repository URL
                    if any(platform in url.lower() for platform in self.PLATFORMS):
                        found_urls.add(url)
        
        return sorted(list(found_urls))
    
    def format_urls_for_display(self, urls: List[str], max_display: int = 3) -> str:
        """
        Format URLs for display in markdown.
        
        Args:
            urls: List of URLs
            max_display: Maximum number of URLs to display
            
        Returns:
            Formatted string for markdown display
        """
        if not urls:
            return "N/A"
        
        # Limit number of displayed URLs
        display_urls = urls[:max_display]
        
        # Create markdown links
        links = []
        for i, url in enumerate(display_urls, 1):
            # Extract platform name for link text
            platform = "Link"
            for p in self.PLATFORMS:
                if p in url.lower():
                    platform = p.split('.')[0].capitalize()
                    break
            links.append(f"[{platform}]({url})")
        
        result = ", ".join(links)
        
        # Add indicator if there are more URLs
        if len(urls) > max_display:
            result += f" (+{len(urls) - max_display} more)"
        
        return result
