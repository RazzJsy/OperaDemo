from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .document_processor import DocumentProcessor
from .retriever import HybridRetriever
from ..llm import create_llm_provider, LLMProvider
from ..validation.validator import MultiStageValidator, ValidationResult


@dataclass
class RAGResponse:
    """Complete RAG response with all metadata"""
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    validation: ValidationResult
    metadata: Dict[str, Any]


class RAGPipeline:
    """
    Complete RAG Pipeline integrating:
    - Document processing
    - Hybrid retrieval
    - LLM generation
    - Multi-stage validation
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        chunk_size: int = 800,
        chunk_overlap: int = 200,
        top_k: int = 5
    ):
        """
        Initialize RAG pipeline
        
        Args:
            llm_provider: LLM provider instance (or create default)
            chunk_size: Document chunk size
            chunk_overlap: Overlap between chunks
            top_k: Number of chunks to retrieve
        """
        print("\nInitializing RAG Pipeline...")
        
        self.document_processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.retriever = HybridRetriever()
        
        self.llm_provider = llm_provider or create_llm_provider()
        
        self.validator = MultiStageValidator()
        
        self.top_k = top_k
        self._documents_loaded = False
        
        print(" RAG Pipeline ready\n")
    
    def load_documents(self, document_path: str, append: bool = False):
        import os
        
        if os.path.isfile(document_path):
            chunks = self.document_processor.process_pdf(document_path)
        elif os.path.isdir(document_path):
            chunks = self.document_processor.process_directory(document_path)
        else:
            raise ValueError(f"Invalid path: {document_path}")
        
        if chunks:
            self.retriever.index_documents(chunks, append=append)
            self._documents_loaded = True
            
            stats = self.retriever.get_stats()
        
            print("\n Index Statistics:")
            print(f" Total chunks: {stats['total_chunks']}")
            print(f" Unique sources: {stats['unique_sources']}")
            print(f" Embedding dims: {stats['embedding_dimensions']}")
        else:
            print(" No chunks created from documents")
    
    def query(
        self,
        question: str,
        return_sources: bool = True,
        validate: bool = True
    ) -> RAGResponse:
        """
        Execute complete RAG query
        
        Args:
            question: User's question
            return_sources: Whether to include source chunks in response
            validate: Whether to run validation framework
            
        Returns:
            RAGResponse with answer, sources, and validation
        """
        if not self._documents_loaded:
            return RAGResponse(
                query=question,
                answer="No documents loaded. Please load documents first.",
                sources=[],
                validation=None,
                metadata={"error": "no_documents_loaded"}
            )
        
        print(f"\n Query: {question}")
        
        print(" 1. Retrieving relevant context...")
        retrieved_chunks = self.retriever.retrieve(
            query=question,
            top_k=self.top_k,
            return_scores=True
        )
        
        if not retrieved_chunks:
            return RAGResponse(
                query=question,
                answer="I could not find relevant information in the documents.",
                sources=[],
                validation=None,
                metadata={"retrieval_count": 0}
            )
        
        print(f"      -> Retrieved {len(retrieved_chunks)} chunks")
        print(f"      -> Top score: {retrieved_chunks[0]['combined_score']:.3f}")
        
        print(" 2. Generating answer with LLM...")
        context_texts = [chunk["text"] for chunk in retrieved_chunks]
        
        llm_response = self.llm_provider.generate(
            prompt=question,
            context=context_texts,
            max_tokens=500,
            temperature=0.1
        )
        
        print(f"      -> Generated {len(llm_response.text.split())} word response")
        
        validation_result = None
        
        if validate:
            print("   3. Running validation framework...")
            validation_result = self.validator.validate(
                query=question,
                answer=llm_response.text,
                retrieved_chunks=retrieved_chunks
            )
            print(f"      -> Validation level: {validation_result.level.value}")
            print(f"      -> Confidence: {validation_result.confidence_score:.2f}")
            
            if validation_result.warnings:
                print(f"      -> Warnings: {len(validation_result.warnings)}")
        
        sources = retrieved_chunks if return_sources else []
        
        response = RAGResponse(
            query=question,
            answer=llm_response.text,
            sources=sources,
            validation=validation_result,
            metadata={
                "retrieval_count": len(retrieved_chunks),
                "model": llm_response.model,
                "tokens_used": llm_response.tokens_used,
                "top_retrieval_score": retrieved_chunks[0]["combined_score"]
            }
        )
        
        print("   Query complete\n")
        
        return response
    
    def batch_query(
        self,
        questions: List[str],
        validate: bool = True
    ) -> List[RAGResponse]:
        """
        Process multiple queries in batch
        
        Useful for evaluation and testing
        """
        responses = []
        
        print(f"\nProcessing {len(questions)} queries...")
        
        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}]")
            response = self.query(question, validate=validate)
            responses.append(response)
        
        return responses
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get statistics about the pipeline"""
        retriever_stats = self.retriever.get_stats()
        
        return {
            "documents_loaded": self._documents_loaded,
            "retriever": retriever_stats,
            "llm_model": self.llm_provider.model_name,
            "chunk_size": self.document_processor.chunk_size,
            "top_k_retrieval": self.top_k
        }