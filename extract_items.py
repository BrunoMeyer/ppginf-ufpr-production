#!/usr/bin/env python3
"""
Script to extract all items from collections in a DSpace community or subcommunity.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv


class DSpaceExtractor:
    """Extractor for DSpace community/subcommunity items."""
    
    def __init__(self, api_url, community_id):
        """
        Initialize the DSpace extractor.
        
        Args:
            api_url: Base URL of the DSpace REST API
            community_id: UUID of the community or subcommunity
        """
        self.api_url = api_url.rstrip('/')
        self.community_id = community_id
        self.session = requests.Session()
        
    def get_collections(self):
        """
        Get all collections in the specified community/subcommunity.
        
        Returns:
            List of collection objects
        """
        url = f"{self.api_url}/core/communities/{self.community_id}/collections"
        collections = []
        page = 0
        
        try:
            while True:
                params = {'page': page, 'size': 20}
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if '_embedded' in data and 'collections' in data['_embedded']:
                    page_collections = data['_embedded']['collections']
                    collections.extend(page_collections)
                    
                    # Check if there are more pages
                    page_info = data.get('page', {})
                    total_pages = page_info.get('totalPages', 1)
                    
                    if page + 1 >= total_pages:
                        break
                    page += 1
                else:
                    break
                    
        except requests.exceptions.RequestException as e:
            print(f"Error fetching collections: {e}", file=sys.stderr)
            return []
            
        return collections
    
    def get_items_from_collection(self, collection_id):
        """
        Get all items from a specific collection.
        
        Args:
            collection_id: UUID of the collection
            
        Returns:
            List of item objects
        """
        url = f"{self.api_url}/core/collections/{collection_id}/items"
        items = []
        page = 0
        
        try:
            while True:
                params = {'page': page, 'size': 20}
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if '_embedded' in data and 'items' in data['_embedded']:
                    page_items = data['_embedded']['items']
                    items.extend(page_items)
                    
                    # Check if there are more pages
                    page_info = data.get('page', {})
                    total_pages = page_info.get('totalPages', 1)
                    
                    if page + 1 >= total_pages:
                        break
                    page += 1
                else:
                    break
                    
        except requests.exceptions.RequestException as e:
            print(f"Error fetching items from collection {collection_id}: {e}", file=sys.stderr)
            return []
            
        return items
    
    def extract_item_data(self, item):
        """
        Extract required data from an item.
        
        Args:
            item: Item object from DSpace API
            
        Returns:
            Dictionary with extracted data
        """
        extracted = {
            'id': item.get('id', ''),
            'uuid': item.get('uuid', ''),
            'name': item.get('name', ''),
            'handle': item.get('handle', ''),
            'metadata': {}
        }
        
        # Extract metadata if available
        if 'metadata' in item:
            for key, values in item['metadata'].items():
                if values:
                    # Store metadata values
                    extracted['metadata'][key] = [v.get('value', '') for v in values]
        
        return extracted
    
    def extract_all_items(self):
        """
        Extract all items from all collections in the community/subcommunity.
        
        Returns:
            Dictionary with collection names as keys and lists of items as values
        """
        print(f"Fetching collections from community: {self.community_id}")
        collections = self.get_collections()
        
        if not collections:
            print("No collections found.")
            return {}
        
        print(f"Found {len(collections)} collection(s)")
        
        result = {}
        
        for collection in collections:
            collection_name = collection.get('name', 'Unknown')
            collection_id = collection.get('id', '')
            
            print(f"\nProcessing collection: {collection_name} (ID: {collection_id})")
            
            items = self.get_items_from_collection(collection_id)
            print(f"  Found {len(items)} item(s)")
            
            extracted_items = [self.extract_item_data(item) for item in items]
            
            result[collection_name] = {
                'collection_id': collection_id,
                'collection_uuid': collection.get('uuid', ''),
                'collection_handle': collection.get('handle', ''),
                'items': extracted_items
            }
        
        return result


def main():
    """Main function to run the extraction."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    api_url = os.getenv('DSPACE_API_URL')
    community_id = os.getenv('COMMUNITY_ID')
    
    if not api_url:
        print("Error: DSPACE_API_URL not set in .env file", file=sys.stderr)
        sys.exit(1)
    
    if not community_id:
        print("Error: COMMUNITY_ID not set in .env file", file=sys.stderr)
        sys.exit(1)
    
    # Create extractor instance
    extractor = DSpaceExtractor(api_url, community_id)
    
    # Extract all items
    print("=" * 80)
    print("DSpace Community/Subcommunity Item Extractor")
    print("=" * 80)
    
    data = extractor.extract_all_items()
    
    # Save results to JSON file
    output_file = 'extracted_items.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 80}")
    print(f"Extraction complete! Data saved to: {output_file}")
    print(f"{'=' * 80}")
    
    # Print summary
    total_items = sum(len(coll['items']) for coll in data.values())
    print(f"\nSummary:")
    print(f"  Collections processed: {len(data)}")
    print(f"  Total items extracted: {total_items}")


if __name__ == '__main__':
    main()
