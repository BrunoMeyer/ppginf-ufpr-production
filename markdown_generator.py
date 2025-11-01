"""
Markdown table generator for thesis and dissertation summaries.
"""
from typing import List, Dict


class MarkdownGenerator:
    """Generator for creating markdown tables from publication data."""
    
    def __init__(self, include_source_urls: bool = False, include_ollama_analysis: bool = False):
        """
        Initialize the markdown generator.
        
        Args:
            include_source_urls: Whether to include source code URLs column
            include_ollama_analysis: Whether to include Ollama analysis section
        """
        self.include_source_urls = include_source_urls
        self.include_ollama_analysis = include_ollama_analysis
        self.headers = ['Author', 'Title', 'URL', 'Summary']
        if include_source_urls:
            self.headers.append('Source Code')
    
    def escape_markdown(self, text: str) -> str:
        """
        Escape special markdown characters in text.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        # Replace pipe characters that would break table structure
        text = text.replace('|', '\\|')
        # Replace newlines with spaces
        text = text.replace('\n', ' ')
        # Collapse multiple spaces
        text = ' '.join(text.split())
        return text
    
    def truncate_text(self, text: str, max_length: int = 200) -> str:
        """
        Truncate text to a maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text with ellipsis if needed
        """
        if len(text) > max_length:
            # Handle Unicode properly by encoding/decoding
            try:
                truncated = text.encode('utf-8')[:max_length - 3].decode('utf-8', 'ignore')
                return truncated + '...'
            except (UnicodeDecodeError, UnicodeEncodeError):
                # Fallback to simple truncation
                return text[:max_length - 3] + '...'
        return text
    
    def generate_table(self, publications: List[Dict[str, str]]) -> str:
        """
        Generate a markdown table from publication data.
        
        Args:
            publications: List of publication dictionaries
            
        Returns:
            Markdown formatted table
        """
        lines = []
        
        # Add header
        lines.append('| ' + ' | '.join(self.headers) + ' |')
        lines.append('|' + '|'.join(['---' for _ in self.headers]) + '|')
        
        # Add rows
        for pub in publications:
            author = self.escape_markdown(pub.get('author', 'Unknown'))
            title = self.escape_markdown(pub.get('title', 'Untitled'))
            url = pub.get('url', '')
            summary = self.escape_markdown(self.truncate_text(pub.get('summary', 'No summary')))
            
            # Format URL as markdown link if available
            url_cell = f'[Link]({url})' if url else 'N/A'
            
            if self.include_source_urls:
                source_urls = pub.get('source_urls', 'N/A')
                row = f"| {author} | {title} | {url_cell} | {summary} | {source_urls} |"
            else:
                row = f"| {author} | {title} | {url_cell} | {summary} |"
            
            lines.append(row)
        
        return '\n'.join(lines)
    
    def generate_document(self, publications: List[Dict[str, str]], title: str = "Production Summary") -> str:
        """
        Generate a complete markdown document with title and table.
        
        Args:
            publications: List of publication dictionaries
            title: Document title
            
        Returns:
            Complete markdown document
        """
        doc_parts = [
            f"# {title}",
            "",
            f"Total publications: {len(publications)}",
            "",
            self.generate_table(publications),
            ""
        ]
        
        # Add Ollama analysis section if enabled
        if self.include_ollama_analysis:
            doc_parts.extend([
                "",
                "---",
                "",
                "# Document Analyses",
                ""
            ])
            
            for i, pub in enumerate(publications, 1):
                analysis = pub.get('ollama_analysis', 'Analysis not available')
                author = pub.get('author', 'Unknown')
                title_text = pub.get('title', 'Untitled')
                
                doc_parts.extend([
                    f"## Document {i}: {title_text}",
                    "",
                    f"**Author:** {author}",
                    "",
                    analysis,
                    "",
                    "---",
                    ""
                ])
        
        return '\n'.join(doc_parts)
