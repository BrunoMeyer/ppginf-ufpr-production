"""
Demo script showing how the tool works with sample data.
This demonstrates the output without needing a real DSpace instance.
"""
from markdown_generator import MarkdownGenerator


def main():
    """Run demo with sample data."""
    # Sample publications data
    sample_publications = [
        {
            'author': 'Silva, Maria da',
            'title': 'Machine Learning Applications in Computer Vision',
            'url': 'https://example.dspace.org/bitstream/handle/123/456/thesis.pdf',
            'summary': 'This thesis presents a comprehensive study of machine learning '
                      'techniques applied to computer vision problems, with focus on '
                      'deep learning architectures for image classification and object detection.'
        },
        {
            'author': 'Santos, João dos',
            'title': 'Distributed Systems: A Study on Consistency Models',
            'url': 'https://example.dspace.org/bitstream/handle/123/457/dissertation.pdf',
            'summary': 'An in-depth analysis of consistency models in distributed systems, '
                      'examining trade-offs between consistency, availability, and partition tolerance.'
        },
        {
            'author': 'Oliveira, Ana Paula',
            'title': 'Natural Language Processing for Portuguese Text Analysis',
            'url': 'https://example.dspace.org/bitstream/handle/123/458/thesis2.pdf',
            'summary': 'This work explores state-of-the-art natural language processing '
                      'techniques adapted for Portuguese language, including named entity '
                      'recognition and sentiment analysis.'
        }
    ]
    
    # Generate markdown
    generator = MarkdownGenerator()
    markdown_content = generator.generate_document(
        sample_publications,
        title="Thesis and Dissertation Production Summary"
    )
    
    # Print to console
    print(markdown_content)
    
    # Save to file
    output_file = "demo_output.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"\n\nDemo output saved to: {output_file}")


if __name__ == '__main__':
    main()
