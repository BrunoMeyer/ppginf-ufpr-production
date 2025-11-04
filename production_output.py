"""
Production output module for saving individual document analysis results.
Saves both summary markdown files and vector representations with metadata.
"""
import os
import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import requests


# Maximum characters to store from extracted text in vector JSON files
MAX_EXTRACTED_TEXT_CHARS = 10000


class ProductionOutput:
    """Manages output of individual document analysis results."""

    def __init__(self, output_dir: str = './production'):
        """
        Initialize production output manager.

        Args:
            output_dir: Directory to store production outputs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _sanitize_filename(self, text: str, max_length: int = 50) -> str:
        """
        Sanitize text for use as filename.

        Args:
            text: Text to sanitize
            max_length: Maximum filename length

        Returns:
            Sanitized filename
        """
        # Remove or replace invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            text = text.replace(char, '_')

        # Remove leading/trailing whitespace and dots
        text = text.strip('. ')

        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length]

        # If empty, use a default
        if not text:
            text = 'untitled'

        return text

    def _generate_doc_id(self, publication: Dict[str, str]) -> str:
        """
        Generate a unique document ID based on publication metadata.

        Note: Uses MD5 for creating a short, consistent ID (not for security).
        MD5 is sufficient here since we're just generating a document identifier
        and collision risk is minimal for typical document collections.

        Args:
            publication: Publication dictionary

        Returns:
            Unique document ID (12-character hex string)
        """
        # Create a hash from title and author for uniqueness
        title = publication.get('title', '')
        author = publication.get('author', '')
        url = publication.get('url', '')

        content = f"{title}:{author}:{url}"
        hash_obj = hashlib.md5(content.encode('utf-8'))
        return hash_obj.hexdigest()[:12]

    def _extract_embedding_from_analysis(self, analysis_text: str) -> Optional[List[float]]:
        """
        Generate an embedding vector for the analysis text using the Ollama embeddings API.

        Environment variables used:
        - OLLAMA_ENDPOINT: base URL of the Ollama server (default http://localhost:11434)
        - OLLAMA_EMBEDDING_MODEL: embedding model name; if not set, falls back to OLLAMA_MODEL

        Args:
            analysis_text: The analysis text

        Returns:
            List of floats representing the embedding, or None if not available or on error
        """
        if not analysis_text or analysis_text == 'Analysis not available':
            return None

        endpoint = os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434').rstrip('/')
        embedding_model = os.getenv('OLLAMA_EMBEDDING_MODEL', os.getenv('OLLAMA_MODEL', 'llama2'))

        url = f"{endpoint}/api/embeddings"
        payload = {
            "model": embedding_model,
            "prompt": analysis_text
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            embedding = data.get('embedding')
            # Some server versions may nest results differently
            if embedding is None and isinstance(data, dict):
                # Try common alternates
                embedding = data.get('data', {}).get('embedding') if isinstance(data.get('data'), dict) else None
            if isinstance(embedding, list):
                # Ensure all elements are float-convertible
                try:
                    return [float(x) for x in embedding]
                except (TypeError, ValueError):
                    return None
            return None
        except requests.exceptions.RequestException as e:
            # Network or server error — skip embeddings silently
            print(f"  Warning: Ollama embeddings request failed: {e}")
            return None
        except ValueError as e:
            # JSON parse error
            print(f"  Warning: Failed to parse embeddings response: {e}")
            return None

    def save_document_summary(self, publication: Dict[str, str], index: int) -> str:
        """
        Save individual document summary as a markdown file.

        Args:
            publication: Publication dictionary with metadata and analysis
            index: Document index/number

        Returns:
            Path to the saved summary file
        """
        # Generate document ID and filename
        doc_id = self._generate_doc_id(publication)
        title_safe = self._sanitize_filename(publication.get('title', 'untitled'))
        filename = f"{index:04d}_{doc_id}_{title_safe}_summary.md"
        filepath = os.path.join(self.output_dir, filename)

        # Build summary content
        author = publication.get('author', 'Unknown')
        title = publication.get('title', 'Untitled')
        url = publication.get('url', 'N/A')
        summary = publication.get('summary', 'No summary available')
        analysis = publication.get('ollama_analysis', 'Analysis not available')
        source_urls = publication.get('source_urls', 'N/A')

        content = f"""# {title}

**Author:** {author}

**URL:** {url}

**Source Code:** {source_urls}

## Summary

{summary}

---

## Full Analysis

{analysis}
"""

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath

    def save_document_vector(self, publication: Dict[str, str],
                           index: int, extracted_text: str = "",
                           ollama_model: str = "unknown") -> str:
        """
        Save document vector representation with metadata as JSON.

        Args:
            publication: Publication dictionary with metadata and analysis
            index: Document index/number
            extracted_text: Full extracted text from the document
            ollama_model: Name of the Ollama model used for analysis

        Returns:
            Path to the saved vector JSON file
        """
        # Generate document ID and filename
        doc_id = self._generate_doc_id(publication)
        title_safe = self._sanitize_filename(publication.get('title', 'untitled'))
        filename = f"{index:04d}_{doc_id}_{title_safe}_vector.json"
        filepath = os.path.join(self.output_dir, filename)

        # Extract or generate embedding vector
        analysis_text = publication.get('ollama_analysis', '')
        embedding = self._extract_embedding_from_analysis(analysis_text)

        # Build vector data structure
        vector_data = {
            'document_id': doc_id,
            'index': index,
            'metadata': {
                'title': publication.get('title', ''),
                'author': publication.get('author', ''),
                'url': publication.get('url', ''),
                'source_urls': publication.get('source_urls', ''),
                'summary': publication.get('summary', ''),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'ollama_model': ollama_model
            },
            'text_data': {
                'extracted_text': extracted_text[:MAX_EXTRACTED_TEXT_CHARS] if extracted_text else "",  # Store first N chars
                'total_characters': len(extracted_text) if extracted_text else 0,
                'analysis_text': analysis_text,
                'analysis_characters': len(analysis_text) if analysis_text else 0
            },
            'vector': {
                'embedding': embedding,
                'embedding_dimension': len(embedding) if embedding else 0,
                'embedding_type': 'statistical_features',  # Placeholder, would be 'ollama_embedding' in production
                'note': 'This is a placeholder embedding based on text statistics. '
                       'In production, use Ollama embedding API for semantic vectors.'
            }
        }

        # Write to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(vector_data, f, indent=2, ensure_ascii=False)

        return filepath

    def save_all_documents(self, publications: List[Dict[str, str]],
                          extracted_texts: Optional[Dict[str, str]] = None,
                          ollama_model: str = "unknown") -> Dict[str, List[str]]:
        """
        Save all document summaries and vectors.

        Args:
            publications: List of publication dictionaries
            extracted_texts: Optional dictionary mapping document URLs to extracted texts
            ollama_model: Name of the Ollama model used for analysis

        Returns:
            Dictionary with 'summaries' and 'vectors' lists of saved file paths
        """
        if extracted_texts is None:
            extracted_texts = {}

        saved_files = {
            'summaries': [],
            'vectors': []
        }

        for i, pub in enumerate(publications, 1):
            # Save summary
            summary_path = self.save_document_summary(pub, i)
            saved_files['summaries'].append(summary_path)

            # Get extracted text for this document
            doc_url = pub.get('url', '')
            doc_text = extracted_texts.get(doc_url, '')

            # Save vector
            vector_path = self.save_document_vector(pub, i, doc_text, ollama_model)
            saved_files['vectors'].append(vector_path)

        return saved_files
