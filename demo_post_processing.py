#!/usr/bin/env python3
"""
Demo script for post-processing analysis feature.
Creates sample documents and runs the full post-processing pipeline.
"""
import os
import json
import tempfile
import shutil
from post_processing import PostProcessor


def create_sample_documents(output_dir: str, n_docs: int = 10):
    """Create sample document vectors for demonstration."""
    import numpy as np
    
    # Sample titles and topics
    topics = {
        'ML': ['Machine Learning Applications', 'Deep Learning for NLP', 'Neural Networks Research'],
        'CV': ['Computer Vision Methods', 'Image Recognition Systems', 'Video Analysis Techniques'],
        'DB': ['Database Optimization', 'Query Processing Algorithms', 'NoSQL Data Management'],
        'SEC': ['Cybersecurity Methods', 'Cryptographic Protocols', 'Network Security Analysis']
    }
    
    all_titles = []
    for topic_list in topics.values():
        all_titles.extend(topic_list)
    
    # Ensure we have enough titles
    while len(all_titles) < n_docs:
        all_titles.append(f"Research Topic {len(all_titles) + 1}")
    
    documents = []
    
    for i in range(n_docs):
        # Create embeddings that cluster by topic
        if i < 3:  # ML cluster
            base_embedding = np.array([0.8, 0.2, 0.1, 0.1, 0.9])
            summary = "This research explores machine learning algorithms and neural network architectures for various applications."
        elif i < 6:  # CV cluster
            base_embedding = np.array([0.2, 0.9, 0.1, 0.1, 0.2])
            summary = "This study focuses on computer vision techniques including object detection and image segmentation."
        elif i < 8:  # DB cluster
            base_embedding = np.array([0.1, 0.1, 0.9, 0.2, 0.1])
            summary = "This work investigates database systems, query optimization, and data management strategies."
        else:  # Security cluster
            base_embedding = np.array([0.1, 0.1, 0.2, 0.9, 0.1])
            summary = "This thesis examines cybersecurity measures, encryption methods, and network protection protocols."
        
        # Add small random noise
        embedding = base_embedding + np.random.randn(5) * 0.05
        embedding = embedding.tolist()
        
        doc = {
            'document_id': f'doc{i+1:03d}',
            'index': i + 1,
            'metadata': {
                'title': all_titles[i],
                'author': f'Author {i+1}',
                'url': f'https://example.com/doc{i+1}.pdf',
                'source_urls': 'N/A',
                'summary': summary,
                'created_at': '2024-01-01T00:00:00Z',
                'ollama_model': 'demo'
            },
            'text_data': {
                'extracted_text': summary * 10,  # Repeat for more text
                'total_characters': len(summary) * 10,
                'analysis_text': summary,
                'analysis_characters': len(summary)
            },
            'vector': {
                'embedding': embedding,
                'embedding_dimension': len(embedding),
                'embedding_type': 'demo',
                'note': 'Demo embeddings for testing'
            }
        }
        
        documents.append(doc)
        
        # Save to file
        filename = f"{i+1:04d}_{doc['document_id']}_test_vector.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(doc, f, indent=2)
    
    return documents


def main():
    """Run post-processing demo."""
    print("=" * 70)
    print("Post-Processing Analysis Demo")
    print("=" * 70)
    
    # Create temporary directory for demo
    demo_dir = tempfile.mkdtemp(prefix='ppginf_demo_')
    print(f"\nCreated demo directory: {demo_dir}")
    
    try:
        # Create sample documents
        print("\nGenerating sample documents...")
        docs = create_sample_documents(demo_dir, n_docs=10)
        print(f"Created {len(docs)} sample documents")
        
        # Initialize post-processor
        # Note: LLM summarization will be skipped if Ollama is not running
        processor = PostProcessor(
            output_dir=demo_dir,
            ollama_endpoint='http://localhost:11434',
            ollama_model='llama2'
        )
        
        # Run full analysis
        print("\nRunning post-processing analysis...")
        print("-" * 70)
        
        output_json = os.path.join(demo_dir, 'demo_results.json')
        output_html = os.path.join(demo_dir, 'demo_visualization.html')
        
        results = processor.run_full_analysis(
            output_json=output_json,
            output_html=output_html,
            n_clusters=4,
            clustering_method='kmeans'
        )
        
        # Display results
        print("\n" + "=" * 70)
        print("Analysis Results Summary")
        print("=" * 70)
        
        if results:
            print(f"\nProcessed {results.get('n_documents', 0)} documents")
            print(f"Embedding dimension: {results.get('embedding_dimension', 0)}")
            print(f"Number of clusters: {results.get('n_clusters', 0)}")
            
            # Show cluster distribution
            if 'cluster_labels' in results:
                import numpy as np
                labels = np.array(results['cluster_labels'])
                print("\nCluster distribution:")
                for cluster_id in range(results.get('n_clusters', 0)):
                    count = np.sum(labels == cluster_id)
                    print(f"  Cluster {cluster_id}: {count} documents")
            
            # Show network stats
            if 'network_graph' in results:
                graph_data = results['network_graph']
                if isinstance(graph_data, dict):
                    print(f"\nNetwork graph:")
                    print(f"  Nodes: {len(graph_data.get('nodes', []))}")
                    print(f"  Edges: {len(graph_data.get('links', []))}")
            
            print(f"\n✓ Analysis results saved to: {output_json}")
            print(f"✓ Visualization saved to: {output_html}")
            
            # List generated word cloud files
            wordclouds = [f for f in os.listdir(demo_dir) if f.endswith('_wordcloud.png')]
            if wordclouds:
                print(f"✓ Generated {len(wordclouds)} word cloud(s)")
            
            print(f"\nYou can view the interactive visualization by opening:")
            print(f"  file://{output_html}")
            
        else:
            print("\nNo results generated (empty analysis)")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Ask if user wants to keep the demo files
        print("\n" + "=" * 70)
        response = input(f"Keep demo files in {demo_dir}? (y/n): ").strip().lower()
        if response != 'y':
            shutil.rmtree(demo_dir)
            print("Demo files cleaned up.")
        else:
            print(f"Demo files preserved in: {demo_dir}")


if __name__ == '__main__':
    main()
