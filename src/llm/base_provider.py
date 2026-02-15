from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized LLM response structure"""
    text: str
    model: str
    tokens_used: Optional[int] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs
    
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        context: List[str],
        max_tokens: int = 500,
        temperature: float = 0.1
    ) -> LLMResponse:
        """
        Generate a response given a prompt and context
        
        Args:
            prompt: The user's question
            context: List of relevant document chunks
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more focused)
            
        Returns:
            LLMResponse object
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the LLM provider is available"""
        pass
    
    def format_prompt(self, prompt: str, context: List[str]) -> str:
        """
        Format the prompt with context for optimal small model performance
        
        Key insight: Small models need very structured prompts
        """
        context_text = "\n\n".join([
            f"[Source {i+1}]\n{chunk}" 
            for i, chunk in enumerate(context)
        ])
        
        formatted_prompt = f"""You are a financial document analysis assistant. Answer the question based ONLY on the provided context.

CONTEXT:
{context_text}

QUESTION: {prompt}

INSTRUCTIONS:
- Answer concisely and accurately
- Only use information from the context above
- If the context doesn't contain the answer, say "I cannot find this information in the provided documents"
- Cite source numbers when making claims (e.g., "According to Source 1...")
- For numerical data, quote exactly as written

ANSWER:"""
        
        return formatted_prompt