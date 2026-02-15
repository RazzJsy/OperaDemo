"""
HuggingFace Inference API Provider

Uses HuggingFace's free tier Inference API for small models.
Optimized for 7B parameter models like Mistral and Phi.
"""

import os
from typing import List
from huggingface_hub import InferenceClient
from .base_provider import LLMProvider, LLMResponse


class HuggingFaceProvider(LLMProvider):
    """
    HuggingFace Inference API provider for small models
    
    Recommended models (7B or smaller):
    - mistralai/Mistral-7B-Instruct-v0.2 (7B, excellent for financial tasks)
    - microsoft/Phi-3-mini-4k-instruct (3.8B, very efficient)
    - google/flan-t5-large (780M, fast but limited)
    """
    
    def __init__(self, model_name: str, api_token: str = None, **kwargs):
        super().__init__(model_name, **kwargs)
        
        self.api_token = api_token or os.getenv("HUGGINGFACE_API_TOKEN")
        self.client = InferenceClient(token=self.api_token, base_url="https://router.huggingface.co")
        
        print(f"Initialized HuggingFace provider with model: {model_name}")
    
    def generate(
        self, 
        prompt: str, 
        context: List[str],
        max_tokens: int = 500,
        temperature: float = 0.1
    ) -> LLMResponse:
        """
        Generate response using HuggingFace Inference API
        """
        try:
            formatted_prompt = self.format_prompt(prompt, context)
            
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": formatted_prompt}],
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            answer_text = response.choices[0].message.content
            
            if "ANSWER:" in answer_text:
                answer_text = answer_text.split("ANSWER:")[-1].strip()
            
            return LLMResponse(
                text=answer_text,
                model=self.model_name,
                tokens_used=None,
                metadata={
                    "provider": "huggingface",
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
        except Exception as e:
            print(f"Error calling HuggingFace API: {e}")
            return LLMResponse(
                text=f"Error generating response: {str(e)}",
                model=self.model_name,
                metadata={"error": str(e)}
            )
    
    def health_check(self) -> bool:
        try:
            response = self.client.chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            model=self.model_name,
            max_tokens=5,
        )
            return response.choices[0].message.content is not None
        except Exception as e:
            print(f"HuggingFace health check failed: {e}")
            return False


class MockProvider(LLMProvider):
    """
    Mock LLM provider for demonstration and testing
    
    This provider simulates LLM responses based on retrieved context,
    allowing the RAG pipeline to be demonstrated without API dependencies.
    """
    
    def __init__(self, model_name: str = "mock-7b", **kwargs):
        super().__init__(model_name, **kwargs)
        print(f"Initialized Mock provider (simulating {model_name})")
    
    def generate(
        self, 
        prompt: str, 
        context: List[str],
        max_tokens: int = 500,
        temperature: float = 0.1
    ) -> LLMResponse:
        """
        Generate a mock response based on context
        
        This demonstrates the RAG pipeline without requiring a real LLM.
        In a real scenario, the actual model would use this same context.
        """
        
        if not context or len(context) == 0:
            answer = "I cannot find this information in the provided documents."
        else:
            answer = self._generate_mock_answer(prompt, context)
        
        return LLMResponse(
            text=answer,
            model=self.model_name,
            tokens_used=len(answer.split()),
            metadata={
                "provider": "mock",
                "context_chunks": len(context),
                "note": "This is a simulated response demonstrating the RAG pipeline"
            }
        )
    
    def _generate_mock_answer(self, prompt: str, context: List[str]) -> str:
        """Generate a realistic mock answer"""
        
        combined_context = " ".join(context[:3])
        words = combined_context.split()
        snippet_length = min(100, len(words))
        snippet = " ".join(words[:snippet_length])
        
        answer = f"""Based on the fund documents, {snippet}...

(Note: This is a demonstration response. With a real 7B model like Mistral-7B-Instruct, 
you would receive a properly synthesized answer extracting specific information from the context.)

The retrieved context contains {len(context)} relevant sections. A production 7B model would:
1. Identify the most relevant information
2. Synthesize a concise answer
3. Cite specific sources
4. Validate numerical accuracy"""
        
        return answer
    
    def health_check(self) -> bool:
        """Mock provider is always available"""
        return True