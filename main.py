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
from pdf_downloader import PDFDownloader
from pdf_text_extractor import PDFTextExtractor
from url_extractor import SourceCodeURLExtractor
from processing_cache import ProcessingCache
from ollama_analyzer import OllamaAnalyzer


def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    endpoint = os.getenv('DSPACE_ENDPOINT')
    community_id = os.getenv('COMMUNITY_ID')
    subcommunity_id = os.getenv('SUBCOMMUNITY_ID')
    output_file = os.getenv('OUTPUT_FILE', 'production_summary.md')
    extract_source_urls = os.getenv('EXTRACT_SOURCE_URLS', 'false').lower() in ('true', '1', 'yes')
    enable_ollama_analysis = os.getenv('ENABLE_OLLAMA_ANALYSIS', 'false').lower() in ('true', '1', 'yes')
    ollama_endpoint = os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434')
    ollama_model = os.getenv('OLLAMA_MODEL', 'llama2')
    
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
    print(f"Extract source URLs: {extract_source_urls}")
    print(f"Ollama analysis enabled: {enable_ollama_analysis}")
    if enable_ollama_analysis:
        print(f"Ollama endpoint: {ollama_endpoint}")
        print(f"Ollama model: {ollama_model}")
    
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
    
    # Extract source code URLs if enabled
    if extract_source_urls:
        print("\nExtracting source code URLs from PDFs...")
        try:
            downloader = PDFDownloader()
            text_extractor = PDFTextExtractor()
            url_extractor = SourceCodeURLExtractor()
            cache = ProcessingCache()
            
            for i, pub in enumerate(publications, 1):
                print(f"\n[{i}/{len(publications)}] Processing: {pub['title'][:50]}...")
                
                # Download PDF
                pdf_path = downloader.download_pdf(pub['url'])
                
                if pdf_path:
                    # Check cache first
                    cached_urls = cache.get_cached_urls(pdf_path)
                    
                    if cached_urls is not None:
                        print(f"  Using cached results (found {len(cached_urls)} URL(s))")
                        if cached_urls:
                            pub['source_urls'] = url_extractor.format_urls_for_display(cached_urls)
                        else:
                            pub['source_urls'] = 'N/A'
                    else:
                        # Extract text from PDF
                        text = text_extractor.extract_text(pdf_path)
                        
                        if text:
                            # Find source code URLs in text
                            source_urls = url_extractor.extract_source_code_urls(text)
                            
                            # Cache the results
                            cache.cache_urls(pdf_path, source_urls)
                            
                            if source_urls:
                                print(f"  Found {len(source_urls)} source code URL(s)")
                                # Format URLs for display
                                pub['source_urls'] = url_extractor.format_urls_for_display(source_urls)
                            else:
                                print(f"  No source code URLs found")
                                pub['source_urls'] = 'N/A'
                        else:
                            # Cache empty result
                            cache.cache_urls(pdf_path, [])
                            pub['source_urls'] = 'N/A'
                else:
                    pub['source_urls'] = 'N/A'
                    
        except ImportError as e:
            print(f"\nError: {e}")
            print("Continuing without source URL extraction...")
            extract_source_urls = False
        except Exception as e:
            print(f"\nError during source URL extraction: {e}")
            print("Continuing without source URL extraction...")
            extract_source_urls = False
    
    # Perform Ollama analysis if enabled
    if enable_ollama_analysis:
        print("\nPerforming Ollama-based document analysis...")
        try:
            analyzer = OllamaAnalyzer(ollama_endpoint, ollama_model)
            
            # Test connection first
            if not analyzer.test_connection():
                print("  Warning: Cannot connect to Ollama. Skipping analysis.")
                enable_ollama_analysis = False
            else:
                downloader = PDFDownloader()
                text_extractor = PDFTextExtractor()
                cache = ProcessingCache()
                
                for i, pub in enumerate(publications, 1):
                    print(f"\n[{i}/{len(publications)}] Analyzing: {pub['title'][:50]}...")
                    
                    # Download PDF if not already done
                    pdf_path = downloader.download_pdf(pub['url'])
                    
                    if pdf_path:
                        # Extract text from PDF
                        text = text_extractor.extract_text(pdf_path)
                        
                        if text and text.strip():
                            # Analyze the document
                            analysis = analyzer.analyze_document(text)
                            
                            if analysis:
                                pub['ollama_analysis'] = analysis
                            else:
                                print(f"  Analysis failed for this document")
                                pub['ollama_analysis'] = 'Analysis not available'
                        else:
                            print(f"  No text extracted, skipping analysis")
                            pub['ollama_analysis'] = 'Analysis not available'
                    else:
                        print(f"  PDF not available, skipping analysis")
                        pub['ollama_analysis'] = 'Analysis not available'
                        
        except ImportError as e:
            print(f"\nError: {e}")
            print("Continuing without Ollama analysis...")
            enable_ollama_analysis = False
        except Exception as e:
            print(f"\nError during Ollama analysis: {e}")
            print("Continuing without Ollama analysis...")
            enable_ollama_analysis = False
    
    # Generate markdown document
    print("\nGenerating markdown document...")
    generator = MarkdownGenerator(
        include_source_urls=extract_source_urls,
        include_ollama_analysis=enable_ollama_analysis
    )
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
