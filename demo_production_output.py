#!/usr/bin/env python3
"""
Demo script to test production output functionality with mock data.
This demonstrates the individual document file generation feature.
"""
import os
import json
import shutil
from production_output import ProductionOutput


def main():
    """Demo the production output functionality."""
    print("Production Output Feature Demo")
    print("=" * 60)
    
    # Create a temporary output directory for the demo
    demo_dir = './demo_production'
    if os.path.exists(demo_dir):
        shutil.rmtree(demo_dir)
    
    # Initialize the production output manager
    output = ProductionOutput(demo_dir)
    print(f"\nOutput directory created: {demo_dir}")
    
    # Create sample publications with mock data
    publications = [
        {
            'title': 'Machine Learning Applications in Healthcare',
            'author': 'Dr. Jane Smith',
            'url': 'https://example.com/doc1.pdf',
            'summary': 'This thesis explores the application of machine learning techniques in medical diagnosis and treatment planning.',
            'source_urls': '[Github](https://github.com/janesmith/ml-healthcare)',
            'ollama_analysis': '''# Document Analysis

## Main Points Summary
This research focuses on applying machine learning algorithms to improve healthcare outcomes.

## Key Themes and Topics
- Medical diagnosis automation
- Treatment planning optimization
- Patient outcome prediction
- Deep learning for medical imaging

## Significant Findings
The research demonstrates that neural networks can achieve 95% accuracy in early disease detection.

## Methodology Overview
The study utilized convolutional neural networks trained on 10,000 medical images.

## Results
Results show significant improvement over traditional diagnostic methods.'''
        },
        {
            'title': 'Blockchain Technology for Supply Chain Management',
            'author': 'Prof. John Doe',
            'url': 'https://example.com/doc2.pdf',
            'summary': 'An investigation into using blockchain technology to improve transparency and efficiency in supply chains.',
            'source_urls': '[Github](https://github.com/johndoe/blockchain-supply), [Gitlab](https://gitlab.com/supply-chain/tracker)',
            'ollama_analysis': '''# Document Analysis

## Main Points Summary
This work examines how blockchain can revolutionize supply chain management.

## Key Themes and Topics
- Distributed ledger technology
- Supply chain transparency
- Smart contracts
- Traceability systems

## Significant Findings
Blockchain implementation reduced fraud by 80% in pilot studies.

## Methodology Overview
A consortium blockchain was developed and tested with 50 companies.

## Results
The system demonstrated improved transparency and reduced operational costs by 30%.'''
        }
    ]
    
    # Mock extracted texts
    extracted_texts = {
        'https://example.com/doc1.pdf': 'Full text of machine learning healthcare research...' * 100,
        'https://example.com/doc2.pdf': 'Full text of blockchain supply chain research...' * 100
    }
    
    # Save all documents
    print("\nSaving document outputs...")
    saved_files = output.save_all_documents(
        publications,
        extracted_texts=extracted_texts,
        ollama_model='llama2-demo'
    )
    
    # Display results
    print(f"\n✓ Saved {len(saved_files['summaries'])} summary files:")
    for path in saved_files['summaries']:
        print(f"  - {os.path.basename(path)}")
    
    print(f"\n✓ Saved {len(saved_files['vectors'])} vector files:")
    for path in saved_files['vectors']:
        print(f"  - {os.path.basename(path)}")
    
    # Show example content
    print("\n" + "=" * 60)
    print("Example Summary File Content:")
    print("=" * 60)
    with open(saved_files['summaries'][0], 'r', encoding='utf-8') as f:
        content = f.read()
        print(content[:500] + "...\n")
    
    print("=" * 60)
    print("Example Vector File Content:")
    print("=" * 60)
    with open(saved_files['vectors'][0], 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(json.dumps(data, indent=2)[:800] + "...\n")
    
    print("=" * 60)
    print(f"\nDemo complete! Check the '{demo_dir}' directory for generated files.")
    print(f"To clean up: rm -rf {demo_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()
