#!/usr/bin/env python3
"""
Main script to extract thesis and dissertation publications from DSpace
and generate a markdown summary table.
"""
import os
import sys
from dotenv import load_dotenv
from dspace_client import DSpaceClient
from markdown_generator import MarkdownGenerator


def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    endpoint = os.getenv('DSPACE_ENDPOINT')
    community_id = os.getenv('COMMUNITY_ID')
    subcommunity_id = os.getenv('SUBCOMMUNITY_ID')
    output_file = os.getenv('OUTPUT_FILE', 'production_summary.md')
    
    # Validate required configuration
    if not endpoint:
        print("Error: DSPACE_ENDPOINT not set in .env file")
        sys.exit(1)
    
    if not community_id:
        print("Error: COMMUNITY_ID not set in .env file")
        sys.exit(1)
    
    print(f"Connecting to DSpace at: {endpoint}")
    print(f"Community ID: {community_id}")
    if subcommunity_id:
        print(f"Subcommunity ID: {subcommunity_id}")
    
    # Initialize DSpace client
    client = DSpaceClient(endpoint)
    
    # Fetch items from DSpace
    print("\nFetching items from DSpace...")
    items = client.get_community_items(community_id, subcommunity_id)
    print(f"Found {len(items)} items")
    
    # Extract metadata from items
    print("\nExtracting metadata...")
    publications = []
    for item in items:
        metadata = client.extract_metadata(item)
        publications.append(metadata)
        # Truncate title for display, handling Unicode properly
        title_preview = metadata['title']
        if len(title_preview) > 50:
            try:
                title_preview = title_preview.encode('utf-8')[:50].decode('utf-8', 'ignore') + '...'
            except (UnicodeDecodeError, UnicodeEncodeError):
                title_preview = title_preview[:50] + '...'
        print(f"  - {title_preview}")
    
    # Generate markdown document
    print("\nGenerating markdown document...")
    generator = MarkdownGenerator()
    markdown_content = generator.generate_document(
        publications, 
        title="Thesis and Dissertation Production Summary"
    )
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"\nMarkdown summary written to: {output_file}")
    print(f"Total publications: {len(publications)}")


if __name__ == '__main__':
    main()
