import os
from typing import Optional
from .base_provider import LLMProvider
from .providers import HuggingFaceProvider, MockProvider


def create_llm_provider(
    provider_type: Optional[str] = None,
    model_name: Optional[str] = None,
    api_token: Optional[str] = None
) -> LLMProvider:
    provider_type = provider_type or os.getenv("LLM_PROVIDER", "huggingface")
    model_name = model_name or os.getenv(
        "LLM_MODEL", 
        "mistralai/Mistral-7B-Instruct-v0.2"
    )
    
    print(f"\nInitializing LLM Provider...")
    print(f"   Provider: {provider_type}")
    print(f"   Model: {model_name}")
    
    if provider_type.lower() == "huggingface":
        return HuggingFaceProvider(
            model_name=model_name,
            api_token=api_token
        )
    elif provider_type.lower() == "mock":
        return MockProvider(model_name=model_name)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


__all__ = [
    "LLMProvider",
    "HuggingFaceProvider", 
    "MockProvider",
    "create_llm_provider"
]
