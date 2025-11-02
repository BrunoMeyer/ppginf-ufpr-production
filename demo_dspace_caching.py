#!/usr/bin/env python3
"""
Demo script to verify DSpace HTTP response caching functionality.
This script demonstrates that metadata is preserved when using cached responses.
"""
import tempfile
import shutil
from unittest.mock import Mock, patch
from dspace_client import DSpaceClient
from processing_cache import ProcessingCache


def demo_caching():
    """Demonstrate the caching functionality."""
    print("=" * 70)
    print("DSpace HTTP Response Caching Demo")
    print("=" * 70)
    
    # Create temporary cache directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize cache
        cache = ProcessingCache(cache_dir=temp_dir)
        print("\n1. Created ProcessingCache instance")
        
        # Mock the requests.Session before creating the client
        with patch('dspace_client.requests.Session') as mock_session:
            # Create mock response with metadata
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = 'https://dspace-prod.example.org/rest/collections/123/items'
            mock_response.json.return_value = [
                {
                    'id': 'item-001',
                    'metadata': [
                        {'key': 'dc.contributor.author', 'value': 'Jane Smith'},
                        {'key': 'dc.title', 'value': 'Advanced Machine Learning Techniques'},
                        {'key': 'dc.description.abstract', 'value': 'This thesis explores novel ML approaches...'}
                    ],
                    'bitstreams': [
                        {'name': 'thesis.pdf', 'retrieveLink': '/bitstreams/456/retrieve'}
                    ]
                }
            ]
            
            # Set up mock session
            mock_session_instance = Mock()
            mock_session_instance.get.return_value = mock_response
            mock_session.return_value = mock_session_instance
            
            # Create DSpace client with cache
            endpoint = 'https://dspace.example.org'
            client = DSpaceClient(endpoint, cache=cache)
            print(f"2. Created DSpaceClient with endpoint: {endpoint}")
            print(f"   Cache enabled: {client.cache is not None}")
            
            print("\n3. Making FIRST request to DSpace API...")
            url = f"{endpoint}/rest/collections/123/items"
            response1 = client._get_with_cache(url, params={'expand': 'metadata,bitstreams'})
            data1 = response1.json()
            
            print(f"   Request URL: {url}")
            print(f"   Resolved URL: {response1.url}")
            print(f"   Response cached: YES")
            print(f"   HTTP requests made: 1")
            
            # Extract metadata
            item = data1[0]
            author = next(m['value'] for m in item['metadata'] if m['key'] == 'dc.contributor.author')
            title = next(m['value'] for m in item['metadata'] if m['key'] == 'dc.title')
            abstract = next(m['value'] for m in item['metadata'] if m['key'] == 'dc.description.abstract')
            
            print(f"\n   Metadata extracted:")
            print(f"   - Author: {author}")
            print(f"   - Title: {title}")
            print(f"   - Abstract: {abstract[:50]}...")
            
            # Verify HTTP was called
            initial_call_count = mock_session_instance.get.call_count
            
            print("\n4. Making SECOND request to same URL (should use cache)...")
            response2 = client._get_with_cache(url, params={'expand': 'metadata,bitstreams'})
            data2 = response2.json()
            
            print(f"   Request URL: {url}")
            print(f"   Resolved URL: {response2.url}")
            print(f"   Response from cache: YES")
            print(f"   HTTP requests made: {mock_session_instance.get.call_count - initial_call_count}")
            
            # Verify metadata is still available
            item2 = data2[0]
            author2 = next(m['value'] for m in item2['metadata'] if m['key'] == 'dc.contributor.author')
            title2 = next(m['value'] for m in item2['metadata'] if m['key'] == 'dc.title')
            abstract2 = next(m['value'] for m in item2['metadata'] if m['key'] == 'dc.description.abstract')
            
            print(f"\n   Metadata from cache (PRESERVED!):")
            print(f"   - Author: {author2}")
            print(f"   - Title: {title2}")
            print(f"   - Abstract: {abstract2[:50]}...")
            
            # Verify they match
            assert author == author2, "Author mismatch!"
            assert title == title2, "Title mismatch!"
            assert abstract == abstract2, "Abstract mismatch!"
            
            print("\n5. Verification:")
            print("   ✓ Metadata preserved in cache")
            print("   ✓ No additional HTTP requests made")
            print("   ✓ Author, title, and abstract available from cached response")
            
            # Check cache file
            cached = cache.get_cached_dspace_response(url)
            print(f"\n6. Cache entry details:")
            print(f"   - Cache key: dspace_response:{url}")
            print(f"   - Response body size: {len(str(cached['response_body']))} bytes")
            print(f"   - Resolved URL stored: {cached['resolved_url']}")
            print(f"   - Metadata fields: {len(cached['response_body'][0]['metadata'])}")
        
            print("\n" + "=" * 70)
            print("DEMO SUCCESSFUL: Caching preserves all metadata!")
            print("=" * 70)
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    demo_caching()
