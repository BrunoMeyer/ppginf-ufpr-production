"""
Ollama-based document text analysis module.
Performs post-processing analysis of academic documents using Ollama LLM.
"""
import requests
from typing import Dict, Optional


class OllamaAnalyzer:
    """Analyzes document text using Ollama API."""
    
    def __init__(self, endpoint: str, model: str):
        """
        Initialize Ollama analyzer.
        
        Args:
            endpoint: Ollama API endpoint URL
            model: Name of the Ollama model to use
        """
        self.endpoint = endpoint.rstrip('/')
        self.model = model
        self.session = requests.Session()
    
    def _call_ollama(self, prompt: str, timeout: int = 300) -> Optional[str]:
        """
        Call Ollama API with a prompt.
        
        Args:
            prompt: The prompt to send to Ollama
            timeout: Request timeout in seconds
            
        Returns:
            Response text from Ollama, or None if request failed
        """
        try:
            url = f"{self.endpoint}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            response = self.session.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
        except requests.exceptions.RequestException as e:
            print(f"  Error calling Ollama API: {e}")
            return None
        except Exception as e:
            print(f"  Unexpected error: {e}")
            return None
    
    def analyze_document(self, text: str) -> Optional[str]:
        """
        Perform comprehensive analysis of document text using Ollama.
        
        This method requests the following analyses:
        1. Summarize the main points of the document
        2. Identify key themes and topics discussed
        3. Highlight significant findings or conclusions
        4. Summarize introduction and objectives
        5. Provide overview of methodology
        6. Outline results and discussions
        7. Conclude with implications and recommendations
        8. Describe research for general audience (press release style)
        9. Generate keywords for indexing
        10. Format output in markdown
        11. List open research questions or future work
        
        Args:
            text: The document text to analyze
            
        Returns:
            Markdown-formatted analysis, or None if analysis failed
        """
        if not text or not text.strip():
            print("  Warning: Empty document text provided")
            return None
        
        # Construct comprehensive prompt
        prompt = f"""You are an academic research analyst. Analyze the following academic document and provide a comprehensive analysis in markdown format.

DOCUMENT TEXT:
{text[:50000]}  

Please provide the following analysis in well-structured markdown format:

# Document Analysis

## 1. Main Points Summary
Summarize the main points of the document.

## 2. Key Themes and Topics
Identify key themes and topics discussed in the document.

## 3. Significant Findings and Conclusions
Highlight any significant findings or conclusions presented by the author.

## 4. Introduction and Objectives
Summarize the introduction and objectives of the research described in the document.

## 5. Methodology Overview
Provide a brief overview of the methodology used in the research.

## 6. Results and Discussions
Outline the results and discussions presented in the document.

## 7. Implications and Recommendations
Conclude with the implications and recommendations made by the author.

## 8. General Audience Summary
Describe the research for a general audience, avoiding technical jargon where possible, in a way that it can be used for a press release or public communication.

## 9. Keywords
Generate a list of potential keywords, separated by semicolons, that accurately represent the content of the document for indexing and search purposes.

## 10. Open Research Questions
List the possible open research questions or future work directions that can be derived from the document.

Provide your analysis now:"""
        
        print("  Sending document to Ollama for analysis...")
        analysis = self._call_ollama(prompt)
        
        if analysis:
            print(f"  Analysis completed ({len(analysis)} characters)")
            return analysis
        else:
            print("  Analysis failed")
            return None
    
    def test_connection(self) -> bool:
        """
        Test connection to Ollama API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.endpoint}/api/tags"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"  Failed to connect to Ollama at {self.endpoint}: {e}")
            return False
