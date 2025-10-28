"""
DSpace API client for extracting thesis and dissertation publications.
"""
import requests
from typing import List, Dict, Optional


# Supported document file types and MIME types
SUPPORTED_FORMATS = {
    'extensions': ['.pdf', '.doc', '.docx'],
    'mime_types': ['application/pdf', 'application/msword', 
                   'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
}


class DSpaceClient:
    """Client for interacting with DSpace REST API."""
    
    def __init__(self, endpoint: str):
        """
        Initialize DSpace client.
        
        Args:
            endpoint: Base URL of the DSpace instance
        """
        self.endpoint = endpoint.rstrip('/')
        self.session = requests.Session()
    
    def get_community_items(self, community_id: str, subcommunity_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch items from a DSpace community or subcommunity.
        
        Args:
            community_id: UUID of the community
            subcommunity_id: Optional UUID of the subcommunity
            
        Returns:
            List of items (thesis/dissertations)
        """
        items = []
        
        # Determine which collection to query
        collection_id = subcommunity_id if subcommunity_id else community_id
        
        # DSpace REST API endpoint for collection items
        # Note: DSpace has different API versions (v6, v7). This uses common patterns.
        try:
            # Try DSpace 6.x/7.x REST API pattern
            url = f"{self.endpoint}/rest/collections/{collection_id}/items"
            response = self.session.get(url, params={'expand': 'metadata,bitstreams'})
            response.raise_for_status()
            items = response.json()
        except requests.exceptions.HTTPError as err:
            # Try alternative API pattern
            print(err)
            try:
                url = f"{self.endpoint}/server/api/core/collections/{collection_id}/items"
                response = self.session.get(url)
                response.raise_for_status()
                data = response.json()
                items = data.get('_embedded', {}).get('items', [])
            except requests.exceptions.RequestException as e:
                print(f"Error fetching items: {e}")
                items = []
        
        return items
    
    def extract_metadata(self, item: Dict) -> Dict[str, str]:
        """
        Extract relevant metadata from a DSpace item.
        
        Args:
            item: DSpace item object
            
        Returns:
            Dictionary with author, title, url, and summary
        """
        metadata = {}
        
        # Extract metadata based on DSpace structure
        # DSpace stores metadata in different formats depending on version
        item_metadata = item.get('metadata', [])
        
        # Helper function to get metadata value
        def get_metadata_value(key: str) -> str:
            if isinstance(item_metadata, list):
                # DSpace 6.x format
                for entry in item_metadata:
                    if entry.get('key') == key:
                        return entry.get('value', '')
            elif isinstance(item_metadata, dict):
                # DSpace 7.x format
                values = item_metadata.get(key, [])
                if values:
                    return values[0].get('value', '') if isinstance(values[0], dict) else str(values[0])
            return ''
        
        # Extract author
        author = (get_metadata_value('dc.contributor.author') or 
                 get_metadata_value('dc.creator') or 
                 'Unknown Author')
        
        # Extract title
        title = (get_metadata_value('dc.title') or 
                get_metadata_value('dc.title.alternative') or 
                'Untitled')
        
        # Extract abstract/summary
        summary = (get_metadata_value('dc.description.abstract') or 
                  get_metadata_value('dc.description') or 
                  'No summary available')
        
        # Extract URL - try to get bitstream URL
        url = ''
        bitstreams = item.get('bitstreams', [])
        if bitstreams:
            # Get the first supported document bitstream if available
            for bitstream in bitstreams:
                name = bitstream.get('name', '').lower()
                mime_type = bitstream.get('format', '')
                
                # Check if file extension or MIME type matches supported formats
                if any(ext in name for ext in SUPPORTED_FORMATS['extensions']) or \
                   mime_type in SUPPORTED_FORMATS['mime_types']:
                    url = f"{self.endpoint}{bitstream.get('retrieveLink', '')}"
                    break
            
            # If no supported format found, use first bitstream
            if not url and bitstreams:
                url = f"{self.endpoint}{bitstreams[0].get('retrieveLink', '')}"
        
        # Fallback to item handle URL
        if not url:
            handle = item.get('handle', '')
            if handle:
                url = f"{self.endpoint}/handle/{handle}"
        
        metadata = {
            'author': author,
            'title': title,
            'url': url,
            'summary': summary
        }
        
        return metadata
