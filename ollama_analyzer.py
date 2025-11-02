"""
Ollama-based document text analysis module.
Performs post-processing analysis of academic documents using Ollama LLM.
"""
import requests
from typing import Dict, Optional
from ollama import Client


class OllamaAnalyzer:
    """Analyzes document text using Ollama API."""
    
    def __init__(self, endpoint: str, model: str, use_client: bool = False):
        """
        Initialize Ollama analyzer.
        
        Args:
            endpoint: Ollama API endpoint URL
            model: Name of the Ollama model to use
        """
        self.endpoint = endpoint.rstrip('/')
        self.model = model
        self.session = requests.Session()
        # Optionally use the official ollama Client when available. Default False to preserve
        # backwards-compatible behavior (the test-suite and older setups expect HTTP calls).
        self.client: Optional[Client] = None
        self.use_client = bool(use_client)
        if self.use_client:
            try:
                # Try a few common constructor signatures for compatibility
                try:
                    # Some versions accept the base URL as the first positional arg
                    self.client = Client(self.endpoint)
                except TypeError:
                    try:
                        # Other versions may use a named parameter
                        self.client = Client(base_url=self.endpoint)
                    except TypeError:
                        # Fallback to default constructor (may use local daemon)
                        self.client = Client()
            except Exception as e:
                # If we couldn't instantiate the client, keep using requests.Session()
                print(f"  Warning: Could not instantiate ollama.Client, falling back to HTTP: {e}")
                self.client = None
    
    def _call_ollama(self, prompt: str, timeout: int = 300) -> Optional[str]:
        """
        Call Ollama API with a prompt.
        
        Args:
            prompt: The prompt to send to Ollama
            timeout: Request timeout in seconds
            
        Returns:
            Response text from Ollama, or None if request failed
        """
        # If we have a client instance, prefer using it (more robust and future-proof)
        if self.client is not None:
            # Try several likely call signatures for client.generate/create_completion without assuming a timeout kwarg
            try:
                if hasattr(self.client, 'generate'):
                    result = None
                    # Try dict-style kwargs first, then positional
                    for call_sig in (
                        {'model': self.model, 'prompt': prompt, 'stream': False},
                        {'model': self.model, 'prompt': prompt},
                        (self.model, prompt),
                    ):
                        try:
                            if isinstance(call_sig, dict):
                                result = self.client.generate(**call_sig)
                            else:
                                result = self.client.generate(*call_sig)
                            break
                        except TypeError:
                            # signature didn't match — try next
                            continue

                    if result is not None:
                        if isinstance(result, str):
                            return result
                        if isinstance(result, dict):
                            return result.get('response') or result.get('text') or result.get('output') or str(result)
                        return str(result)

                if hasattr(self.client, 'create_completion'):
                    result = None
                    for call_sig in (
                        {'model': self.model, 'prompt': prompt},
                        (self.model, prompt),
                    ):
                        try:
                            if isinstance(call_sig, dict):
                                result = self.client.create_completion(**call_sig)
                            else:
                                result = self.client.create_completion(*call_sig)
                            break
                        except TypeError:
                            continue

                    if result is not None:
                        if isinstance(result, dict):
                            return result.get('response') or result.get('text') or str(result)
                        return str(result)

            except (TypeError, AttributeError) as e:
                print(f"  Ollama client call failed, falling back to HTTP: {e}")

        # Fallback: use direct HTTP to the Ollama API endpoint (keeps previous behavior)
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
            # Ollama HTTP response commonly contains 'response'
            return result.get('response', '')
        except requests.exceptions.RequestException as e:
            print(f"  Error calling Ollama API over HTTP: {e}")
            return None
        except Exception as e:
            print(f"  Unexpected error calling Ollama API over HTTP: {e}")
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
        
        print(f"  Sending document to Ollama for analysis... (len={len(text)} characters)")
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
