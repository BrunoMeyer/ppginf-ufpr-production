"""
Unit tests for post_processing module.
"""
import unittest
import os
import json
import tempfile
import shutil
import numpy as np
from post_processing import PostProcessor


class TestPostProcessor(unittest.TestCase):
    """Test cases for PostProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.processor = PostProcessor(output_dir=self.test_dir)
        
        # Create sample document vectors
        self.sample_vectors = [
            {
                'document_id': 'doc1',
                'index': 1,
                'metadata': {
                    'title': 'Machine Learning Applications',
                    'author': 'John Doe',
                    'summary': 'This paper discusses machine learning algorithms and their applications.'
                },
                'vector': {
                    'embedding': [0.1, 0.2, 0.3, 0.4, 0.5],
                    'embedding_dimension': 5
                }
            },
            {
                'document_id': 'doc2',
                'index': 2,
                'metadata': {
                    'title': 'Deep Learning for NLP',
                    'author': 'Jane Smith',
                    'summary': 'This research explores deep learning techniques for natural language processing.'
                },
                'vector': {
                    'embedding': [0.2, 0.3, 0.4, 0.5, 0.6],
                    'embedding_dimension': 5
                }
            },
            {
                'document_id': 'doc3',
                'index': 3,
                'metadata': {
                    'title': 'Computer Vision Research',
                    'author': 'Bob Johnson',
                    'summary': 'This study focuses on computer vision and image recognition methods.'
                },
                'vector': {
                    'embedding': [0.9, 0.8, 0.7, 0.6, 0.5],
                    'embedding_dimension': 5
                }
            }
        ]
        
        # Save sample vectors to test directory
        for vec in self.sample_vectors:
            filename = f"{vec['index']:04d}_{vec['document_id']}_test_vector.json"
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(vec, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_load_document_vectors(self):
        """Test loading document vectors from directory."""
        vectors = self.processor.load_document_vectors()
        self.assertEqual(len(vectors), 3)
        self.assertEqual(vectors[0]['document_id'], 'doc1')
    
    def test_extract_embeddings_matrix(self):
        """Test extracting embeddings as numpy matrix."""
        vectors = self.processor.load_document_vectors()
        embeddings = self.processor.extract_embeddings_matrix(vectors)
        
        self.assertEqual(embeddings.shape, (3, 5))
        np.testing.assert_array_almost_equal(embeddings[0], [0.1, 0.2, 0.3, 0.4, 0.5])
    
    def test_cluster_documents_kmeans(self):
        """Test K-means clustering."""
        vectors = self.processor.load_document_vectors()
        embeddings = self.processor.extract_embeddings_matrix(vectors)
        
        labels = self.processor.cluster_documents(embeddings, n_clusters=2, method='kmeans')
        
        self.assertEqual(len(labels), 3)
        self.assertIn(labels[0], [0, 1])
    
    def test_cluster_documents_auto(self):
        """Test automatic cluster number determination."""
        vectors = self.processor.load_document_vectors()
        embeddings = self.processor.extract_embeddings_matrix(vectors)
        
        labels = self.processor.cluster_documents(embeddings, n_clusters=None)
        
        self.assertEqual(len(labels), 3)
    
    def test_compute_similarity_matrix(self):
        """Test similarity matrix computation."""
        vectors = self.processor.load_document_vectors()
        embeddings = self.processor.extract_embeddings_matrix(vectors)
        
        similarity = self.processor.compute_similarity_matrix(embeddings, metric='cosine')
        
        self.assertEqual(similarity.shape, (3, 3))
        # Diagonal should be 1 (self-similarity)
        np.testing.assert_array_almost_equal(np.diag(similarity), [1.0, 1.0, 1.0])
        # Matrix should be symmetric
        np.testing.assert_array_almost_equal(similarity, similarity.T)
    
    def test_create_network_graph(self):
        """Test network graph creation."""
        vectors = self.processor.load_document_vectors()
        embeddings = self.processor.extract_embeddings_matrix(vectors)
        similarity = self.processor.compute_similarity_matrix(embeddings)
        
        doc_ids = [v['document_id'] for v in vectors]
        graph = self.processor.create_network_graph(similarity, doc_ids, threshold=0.5)
        
        self.assertEqual(graph.number_of_nodes(), 3)
        self.assertGreaterEqual(graph.number_of_edges(), 0)
    
    def test_apply_tsne(self):
        """Test t-SNE dimensionality reduction."""
        # Create more samples for t-SNE (needs at least perplexity + 1 samples)
        # Generate 10 samples with 5 dimensions each
        np.random.seed(42)
        embeddings = np.random.rand(10, 5)
        
        tsne_coords = self.processor.apply_tsne(embeddings, n_components=2, perplexity=3)
        
        self.assertEqual(tsne_coords.shape, (10, 2))
    
    def test_generate_wordcloud(self):
        """Test word cloud generation."""
        text = "machine learning algorithms data science artificial intelligence"
        output_path = os.path.join(self.test_dir, 'test_wordcloud.png')
        
        result = self.processor.generate_wordcloud(text, output_path)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_path))
    
    def test_generate_wordcloud_empty_text(self):
        """Test word cloud with empty text."""
        output_path = os.path.join(self.test_dir, 'test_wordcloud_empty.png')
        
        result = self.processor.generate_wordcloud("", output_path)
        
        self.assertFalse(result)
        self.assertFalse(os.path.exists(output_path))
    
    def test_save_analysis_results(self):
        """Test saving analysis results to JSON."""
        results = {
            'n_documents': 3,
            'cluster_labels': np.array([0, 0, 1]),
            'tsne_coordinates': np.array([[1.0, 2.0], [1.5, 2.5], [3.0, 4.0]])
        }
        
        output_path = os.path.join(self.test_dir, 'results.json')
        success = self.processor.save_analysis_results(output_path, results)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify content
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['n_documents'], 3)
        self.assertEqual(len(saved_data['cluster_labels']), 3)
    
    def test_create_visualization_html(self):
        """Test HTML visualization creation."""
        results = {
            'tsne_coordinates': [[1.0, 2.0], [1.5, 2.5], [3.0, 4.0]],
            'cluster_labels': [0, 0, 1],
            'document_metadata': [
                {'title': 'Doc 1', 'author': 'Author 1'},
                {'title': 'Doc 2', 'author': 'Author 2'},
                {'title': 'Doc 3', 'author': 'Author 3'}
            ],
            'network_graph': {
                'nodes': [{'id': 'doc1'}, {'id': 'doc2'}, {'id': 'doc3'}],
                'links': [{'source': 'doc1', 'target': 'doc2', 'weight': 0.8}]
            }
        }
        
        output_path = os.path.join(self.test_dir, 'viz.html')
        success = self.processor.create_visualization_html(results, output_path)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_path))
        
        # Verify HTML content
        with open(output_path, 'r') as f:
            html_content = f.read()
        
        self.assertIn('Document Analysis Visualization', html_content)
        self.assertIn('t-SNE', html_content)
        self.assertIn('vis-network', html_content)
    
    def test_empty_directory(self):
        """Test with empty directory."""
        empty_dir = tempfile.mkdtemp()
        processor = PostProcessor(output_dir=empty_dir)
        
        vectors = processor.load_document_vectors()
        self.assertEqual(len(vectors), 0)
        
        shutil.rmtree(empty_dir)
    
    def test_invalid_embeddings(self):
        """Test handling of documents without embeddings."""
        invalid_vec = {
            'document_id': 'doc_invalid',
            'index': 4,
            'metadata': {'title': 'Invalid', 'author': 'Unknown', 'summary': 'Test'},
            'vector': {'embedding': None}
        }
        
        filename = f"0004_doc_invalid_test_vector.json"
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(invalid_vec, f)
        
        vectors = self.processor.load_document_vectors()
        embeddings = self.processor.extract_embeddings_matrix(vectors)
        
        # Should only have 3 valid embeddings
        self.assertEqual(len(embeddings), 3)


if __name__ == '__main__':
    unittest.main()
