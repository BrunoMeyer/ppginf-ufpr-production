"""
Post-processing analysis module for document embeddings.
Performs clustering, network analysis, dimensionality reduction, and visualization.
"""
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import requests

# Scientific computing libraries
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import networkx as nx

# Visualization libraries
from wordcloud import WordCloud
import plotly.express as px


class PostProcessor:
    """Post-processing analysis for document embeddings and metadata."""
    
    def __init__(self, output_dir: str = './production', 
                 ollama_endpoint: str = 'http://localhost:11434',
                 ollama_model: str = 'llama2'):
        """
        Initialize post-processor.
        
        Args:
            output_dir: Directory containing production output files
            ollama_endpoint: Ollama API endpoint for LLM analysis
            ollama_model: Ollama model name
        """
        self.output_dir = output_dir
        self.ollama_endpoint = ollama_endpoint.rstrip('/')
        self.ollama_model = ollama_model
        
    def load_document_vectors(self) -> List[Dict[str, Any]]:
        """
        Load all document vector files from production directory.
        
        Returns:
            List of document vector dictionaries
        """
        vectors = []
        if not os.path.exists(self.output_dir):
            return vectors
            
        for filename in sorted(os.listdir(self.output_dir)):
            if filename.endswith('_vector.json'):
                filepath = os.path.join(self.output_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        vectors.append(data)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Failed to load {filename}: {e}")
                    
        return vectors
    
    def extract_embeddings_matrix(self, vectors: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extract embedding vectors as a numpy matrix.
        
        Args:
            vectors: List of document vector dictionaries
            
        Returns:
            Numpy array of shape (n_documents, embedding_dim)
        """
        embeddings = []
        for doc in vectors:
            embedding = doc.get('vector', {}).get('embedding')
            if embedding and isinstance(embedding, list):
                embeddings.append(embedding)
            else:
                # If no embedding, use zero vector (will be filtered later)
                embeddings.append([])
                
        # Filter out empty embeddings and ensure consistent dimensions
        valid_embeddings = [e for e in embeddings if len(e) > 0]
        
        if not valid_embeddings:
            return np.array([])
            
        # Check if all embeddings have the same dimension
        dimensions = [len(e) for e in valid_embeddings]
        if len(set(dimensions)) > 1:
            print(f"Warning: Inconsistent embedding dimensions: {set(dimensions)}")
            # Use the most common dimension
            target_dim = Counter(dimensions).most_common(1)[0][0]
            valid_embeddings = [e for e in valid_embeddings if len(e) == target_dim]
            
        return np.array(valid_embeddings)
    
    def cluster_documents(self, embeddings: np.ndarray, 
                         n_clusters: Optional[int] = None,
                         method: str = 'kmeans') -> np.ndarray:
        """
        Cluster document embeddings using unsupervised learning.
        
        Args:
            embeddings: Embedding matrix (n_documents, embedding_dim)
            n_clusters: Number of clusters (auto-determined if None)
            method: Clustering method ('kmeans' or 'dbscan')
            
        Returns:
            Cluster labels array
        """
        if len(embeddings) == 0:
            return np.array([])
            
        # Auto-determine number of clusters if not specified
        if n_clusters is None:
            # Use square root heuristic
            n_clusters = max(2, int(np.sqrt(len(embeddings))))
            
        if method == 'kmeans':
            # Normalize embeddings before clustering
            scaler = StandardScaler()
            embeddings_scaled = scaler.fit_transform(embeddings)
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings_scaled)
            
        elif method == 'dbscan':
            # DBSCAN auto-determines number of clusters
            dbscan = DBSCAN(eps=0.5, min_samples=2, metric='cosine')
            labels = dbscan.fit_predict(embeddings)
            
        else:
            raise ValueError(f"Unknown clustering method: {method}")
            
        return labels
    
    def generate_wordcloud(self, text: str, output_path: str) -> bool:
        """
        Generate a word cloud from text and save to file.
        
        Args:
            text: Input text for word cloud
            output_path: Path to save word cloud image
            
        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            return False
            
        try:
            wordcloud = WordCloud(
                width=800, 
                height=400,
                background_color='white',
                max_words=100,
                relative_scaling=0.5,
                min_font_size=10
            ).generate(text)
            
            wordcloud.to_file(output_path)
            return True
            
        except Exception as e:
            print(f"Warning: Failed to generate word cloud: {e}")
            return False
    
    def summarize_cluster_with_llm(self, titles: List[str], 
                                   summaries: List[str]) -> Optional[str]:
        """
        Use LLM to describe and summarize what a cluster represents.
        
        Args:
            titles: List of document titles in cluster
            summaries: List of document summaries in cluster
            
        Returns:
            LLM-generated cluster summary, or None if failed
        """
        # Concatenate titles and summaries
        combined_text = "DOCUMENT TITLES:\n"
        combined_text += "\n".join(f"- {title}" for title in titles)
        combined_text += "\n\nDOCUMENT SUMMARIES:\n"
        combined_text += "\n\n".join(summaries)
        
        prompt = f"""You are analyzing a cluster of academic documents. Based on the following titles and summaries, provide a concise description of what this cluster represents. What is the common theme or research area?

{combined_text[:5000]}

Provide a 2-3 sentence summary describing the common theme of these documents:"""
        
        try:
            url = f"{self.ollama_endpoint}/api/generate"
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except Exception as e:
            print(f"Warning: LLM cluster summary failed: {e}")
            return None
    
    def compute_similarity_matrix(self, embeddings: np.ndarray, 
                                  metric: str = 'cosine') -> np.ndarray:
        """
        Compute pairwise similarity/distance matrix for documents.
        
        Args:
            embeddings: Embedding matrix (n_documents, embedding_dim)
            metric: Similarity metric ('cosine', 'euclidean', 'correlation')
            
        Returns:
            Similarity matrix (n_documents, n_documents)
        """
        if len(embeddings) == 0:
            return np.array([[]])
            
        if metric == 'cosine':
            # Cosine similarity (higher is more similar)
            similarity = cosine_similarity(embeddings)
            
        elif metric == 'euclidean':
            # Convert distance to similarity (inverse)
            distances = euclidean_distances(embeddings)
            # Normalize to [0, 1] range and invert
            max_dist = np.max(distances)
            if max_dist > 0:
                similarity = 1 - (distances / max_dist)
            else:
                similarity = np.ones_like(distances)
                
        elif metric == 'correlation':
            # Pearson correlation as similarity
            from scipy.stats import pearsonr
            n_docs = len(embeddings)
            similarity = np.zeros((n_docs, n_docs))
            for i in range(n_docs):
                for j in range(n_docs):
                    if i == j:
                        similarity[i, j] = 1.0
                    else:
                        corr, _ = pearsonr(embeddings[i], embeddings[j])
                        similarity[i, j] = corr
                        
        else:
            raise ValueError(f"Unknown metric: {metric}")
            
        return similarity
    
    def create_network_graph(self, similarity_matrix: np.ndarray,
                            doc_ids: List[str],
                            threshold: float = 0.7) -> nx.Graph:
        """
        Create a network graph from similarity matrix.
        
        Args:
            similarity_matrix: Pairwise similarity matrix
            doc_ids: List of document IDs
            threshold: Minimum similarity to create edge
            
        Returns:
            NetworkX graph object
        """
        G = nx.Graph()
        
        # Add nodes
        for doc_id in doc_ids:
            G.add_node(doc_id)
            
        # Add edges for similarities above threshold
        n_docs = len(doc_ids)
        for i in range(n_docs):
            for j in range(i + 1, n_docs):
                similarity = similarity_matrix[i, j]
                if similarity >= threshold:
                    G.add_edge(doc_ids[i], doc_ids[j], weight=similarity)
                    
        return G
    
    def apply_tsne(self, embeddings: np.ndarray, 
                  n_components: int = 2,
                  perplexity: int = 30,
                  random_state: int = 42) -> np.ndarray:
        """
        Apply t-SNE dimensionality reduction to embeddings.
        
        Args:
            embeddings: High-dimensional embeddings
            n_components: Target dimensions (typically 2 for visualization)
            perplexity: t-SNE perplexity parameter
            random_state: Random seed for reproducibility
            
        Returns:
            Low-dimensional embedding matrix
        """
        if len(embeddings) == 0:
            return np.array([])
            
        # Adjust perplexity if needed (must be less than n_samples)
        max_perplexity = len(embeddings) - 1
        if perplexity >= max_perplexity:
            perplexity = max(5, max_perplexity // 2)
            
        tsne = TSNE(
            n_components=n_components,
            perplexity=perplexity,
            random_state=random_state,
            max_iter=1000
        )
        
        return tsne.fit_transform(embeddings)
    
    def save_analysis_results(self, output_path: str, results: Dict[str, Any]) -> bool:
        """
        Save analysis results to JSON file.
        
        Args:
            output_path: Path to output JSON file
            results: Dictionary containing all analysis results
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert numpy arrays to lists for JSON serialization
            serializable_results = {}
            for key, value in results.items():
                if isinstance(value, np.ndarray):
                    # Convert to Python list, handling numpy types
                    serializable_results[key] = value.tolist()
                elif isinstance(value, (np.integer, np.floating)):
                    # Convert numpy scalars to Python types
                    serializable_results[key] = value.item()
                elif isinstance(value, nx.Graph):
                    # Convert graph to node-link format
                    serializable_results[key] = nx.node_link_data(value, edges="links")
                elif isinstance(value, dict):
                    # Recursively handle dictionaries
                    serializable_results[key] = self._make_json_serializable(value)
                else:
                    serializable_results[key] = value
                    
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            print(f"Error saving analysis results: {e}")
            return False
    
    def _make_json_serializable(self, obj):
        """Recursively convert objects to JSON-serializable format."""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        else:
            return obj
    
    def create_visualization_html(self, results: Dict[str, Any], 
                                  output_path: str) -> bool:
        """
        Create interactive HTML visualization with vis.js and Plotly.
        
        Args:
            results: Analysis results dictionary
            output_path: Path to output HTML file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract data from results
            tsne_coords = results.get('tsne_coordinates', [])
            cluster_labels = results.get('cluster_labels', [])
            doc_metadata = results.get('document_metadata', [])
            network_graph = results.get('network_graph', {})
            
            # Create t-SNE scatter plot with Plotly
            if len(tsne_coords) > 0 and len(cluster_labels) > 0:
                tsne_array = np.array(tsne_coords)
                
                # Prepare data for plotting
                titles = [doc.get('title', 'Unknown')[:50] for doc in doc_metadata]
                
                fig = px.scatter(
                    x=tsne_array[:, 0],
                    y=tsne_array[:, 1],
                    color=[str(label) for label in cluster_labels],
                    hover_name=titles,
                    labels={'x': 't-SNE Dimension 1', 'y': 't-SNE Dimension 2', 'color': 'Cluster'},
                    title='Document Clusters (t-SNE Visualization)'
                )
                
                fig.update_traces(marker=dict(size=10, opacity=0.7))
                fig.update_layout(
                    width=900,
                    height=600,
                    hovermode='closest'
                )
                
                # Save plot as HTML component
                plot_html = fig.to_html(include_plotlyjs='cdn', div_id='tsne-plot')
            else:
                plot_html = "<p>No t-SNE data available</p>"
            
            # Create network graph visualization with vis.js
            if network_graph and 'nodes' in network_graph and 'links' in network_graph:
                nodes_json = json.dumps(network_graph['nodes'])
                edges_json = json.dumps([
                    {'from': link['source'], 'to': link['target'], 
                     'value': link.get('weight', 1)}
                    for link in network_graph['links']
                ])
                
                network_html = f"""
                <div id="network" style="width: 100%; height: 600px; border: 1px solid #ddd;"></div>
                <script type="text/javascript">
                  var nodes = new vis.DataSet({nodes_json});
                  var edges = new vis.DataSet({edges_json});
                  var container = document.getElementById('network');
                  var data = {{
                    nodes: nodes,
                    edges: edges
                  }};
                  var options = {{
                    nodes: {{
                      shape: 'dot',
                      size: 16,
                      font: {{ size: 12 }},
                      borderWidth: 2
                    }},
                    edges: {{
                      width: 0.15,
                      smooth: {{ type: 'continuous' }}
                    }},
                    physics: {{
                      stabilization: false,
                      barnesHut: {{
                        gravitationalConstant: -2000,
                        springConstant: 0.001,
                        springLength: 200
                      }}
                    }}
                  }};
                  var network = new vis.Network(container, data, options);
                </script>
                """
            else:
                network_html = "<p>No network graph data available</p>"
            
            # Create complete HTML document
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Document Analysis Visualization</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background-color: #f5f5f5;
                    }}
                    h1, h2 {{
                        color: #333;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .section {{
                        margin: 30px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Document Analysis Visualization</h1>
                    
                    <div class="section">
                        <h2>t-SNE Cluster Visualization</h2>
                        {plot_html}
                    </div>
                    
                    <div class="section">
                        <h2>Document Correlation Network</h2>
                        {network_html}
                    </div>
                </div>
            </body>
            </html>
            """
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            return True
            
        except Exception as e:
            print(f"Error creating visualization HTML: {e}")
            return False
    
    def run_full_analysis(self, output_json: str = 'analysis_results.json',
                         output_html: str = 'visualization.html',
                         n_clusters: Optional[int] = None,
                         clustering_method: str = 'kmeans',
                         similarity_metric: str = 'cosine',
                         network_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Run complete post-processing analysis pipeline.
        
        Args:
            output_json: Path to save analysis results JSON
            output_html: Path to save visualization HTML
            n_clusters: Number of clusters (auto if None)
            clustering_method: Clustering algorithm
            similarity_metric: Similarity metric for network
            network_threshold: Minimum similarity for network edges
            
        Returns:
            Dictionary containing all analysis results
        """
        print("Starting post-processing analysis...")
        
        # Load document vectors
        print("Loading document vectors...")
        vectors = self.load_document_vectors()
        print(f"Loaded {len(vectors)} documents")
        
        if len(vectors) == 0:
            print("No documents found. Exiting.")
            return {}
        
        # Extract embeddings
        print("Extracting embeddings...")
        embeddings = self.extract_embeddings_matrix(vectors)
        print(f"Embedding matrix shape: {embeddings.shape}")
        
        if len(embeddings) == 0:
            print("No valid embeddings found. Exiting.")
            return {}
        
        # Perform clustering
        print(f"Clustering documents using {clustering_method}...")
        cluster_labels = self.cluster_documents(
            embeddings, 
            n_clusters=n_clusters,
            method=clustering_method
        )
        n_clusters_found = len(set(cluster_labels))
        print(f"Found {n_clusters_found} clusters")
        
        # Process each cluster
        cluster_summaries = {}
        cluster_wordclouds = {}
        
        for cluster_id in set(cluster_labels):
            if cluster_id == -1:  # DBSCAN noise cluster
                continue
                
            print(f"\nProcessing cluster {cluster_id}...")
            
            # Get documents in this cluster
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            cluster_docs = [vectors[i] for i in cluster_indices]
            
            # Extract titles and summaries
            titles = [doc['metadata']['title'] for doc in cluster_docs]
            summaries = [doc['metadata']['summary'] for doc in cluster_docs]
            
            # Generate word cloud
            combined_text = " ".join(summaries)
            wordcloud_path = f"cluster_{cluster_id}_wordcloud.png"
            if self.generate_wordcloud(combined_text, wordcloud_path):
                cluster_wordclouds[cluster_id] = wordcloud_path
                print(f"  Generated word cloud: {wordcloud_path}")
            
            # Get LLM summary of cluster
            llm_summary = self.summarize_cluster_with_llm(titles, summaries)
            if llm_summary:
                cluster_summaries[cluster_id] = llm_summary
                print(f"  LLM summary: {llm_summary[:100]}...")
        
        # Compute similarity matrix
        print("\nComputing similarity matrix...")
        similarity_matrix = self.compute_similarity_matrix(
            embeddings, 
            metric=similarity_metric
        )
        
        # Create network graph
        print("Creating network graph...")
        doc_ids = [vec['document_id'] for vec in vectors]
        network_graph = self.create_network_graph(
            similarity_matrix, 
            doc_ids,
            threshold=network_threshold
        )
        print(f"Network has {network_graph.number_of_nodes()} nodes and {network_graph.number_of_edges()} edges")
        
        # Apply t-SNE
        print("Applying t-SNE dimensionality reduction...")
        tsne_coords = self.apply_tsne(embeddings)
        
        # Compile results
        results = {
            'n_documents': len(vectors),
            'embedding_dimension': embeddings.shape[1] if len(embeddings) > 0 else 0,
            'n_clusters': n_clusters_found,
            'cluster_labels': cluster_labels,
            'cluster_summaries': cluster_summaries,
            'cluster_wordclouds': cluster_wordclouds,
            'similarity_matrix': similarity_matrix,
            'network_graph': network_graph,
            'tsne_coordinates': tsne_coords,
            'document_metadata': [
                {
                    'document_id': vec['document_id'],
                    'title': vec['metadata']['title'],
                    'author': vec['metadata']['author']
                }
                for vec in vectors
            ]
        }
        
        # Save results to JSON
        print(f"\nSaving results to {output_json}...")
        self.save_analysis_results(output_json, results)
        
        # Create visualization
        print(f"Creating visualization at {output_html}...")
        self.create_visualization_html(results, output_html)
        
        print("\nPost-processing analysis complete!")
        return results
