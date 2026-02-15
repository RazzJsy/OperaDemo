"""
Hybrid Retrieval Engine - Combines sparse (BM25) and dense (embeddings) retrieval

Why hybrid?
- BM25: Excellent for exact keyword matches (e.g., "management fee", specific numbers)
- Dense embeddings: Great for semantic similarity (e.g., "investment strategy" vs "portfolio approach")
- Combined: Best of both worlds for financial documents
"""

from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from sklearn.metrics.pairwise import cosine_similarity
from .document_processor import DocumentChunk


class HybridRetriever:
    """
    Hybrid retrieval combining BM25 (sparse) and embeddings (dense)
    
    This is where the "magic" happens for small model performance:
    Better retrieval = better context = better answers from smaller models
    """
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        bm25_weight: float = 0.5,
        dense_weight: float = 0.5
    ):
        """
        Initialize hybrid retriever
        
        Args:
            embedding_model: SentenceTransformer model for dense embeddings
            bm25_weight: Weight for BM25 scores (0-1)
            dense_weight: Weight for dense scores (0-1)
        """
        print(f"\nInitializing Hybrid Retriever...")
        print(f"   Embedding model: {embedding_model}")
        
        self.embedding_model = SentenceTransformer(embedding_model)
        self.bm25_weight = bm25_weight
        self.dense_weight = dense_weight
        self.chunks: List[DocumentChunk] = []
        self.chunk_embeddings: np.ndarray = None
        self.bm25: BM25Okapi = None
        
        print("   Retriever initialized")
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        return_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining BM25 and dense similarity
        
        Args:
            query: Search query
            top_k: Number of results to return
            return_scores: Whether to include retrieval scores
            
        Returns:
            List of retrieved chunks with metadata
        """
        if not self.chunks or self.bm25 is None:
            print(" No documents indexed")
            return []
        
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        query_embedding = self.embedding_model.encode([query])[0]
        dense_scores = cosine_similarity(
            [query_embedding], 
            self.chunk_embeddings
        )[0]
        
        bm25_scores_norm = self._normalize_scores(bm25_scores)
        dense_scores_norm = self._normalize_scores(dense_scores)
        
        combined_scores = (
            self.bm25_weight * bm25_scores_norm + 
            self.dense_weight * dense_scores_norm
        )
        
        top_indices = np.argsort(combined_scores)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx]
            
            result = {
                "chunk": chunk,
                "text": chunk.text,
                "source": chunk.source,
                "page": chunk.page,
                "chunk_id": chunk.chunk_id
            }
            
            if return_scores:
                result.update({
                    "combined_score": float(combined_scores[idx]),
                    "bm25_score": float(bm25_scores_norm[idx]),
                    "dense_score": float(dense_scores_norm[idx])
                })
            
            results.append(result)
        
        return results
    
    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normalize scores to 0-1 range"""
        if len(scores) == 0:
            return scores
        
        min_score = scores.min()
        max_score = scores.max()
        
        if max_score - min_score == 0:
            return np.ones_like(scores)
        
        return (scores - min_score) / (max_score - min_score)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics"""
        return {
            "total_chunks": len(self.chunks),
            "embedding_dimensions": self.chunk_embeddings.shape[1] if self.chunk_embeddings is not None else 0,
            "bm25_indexed": self.bm25 is not None,
            "unique_sources": len(set(c.source for c in self.chunks))
        }
    
    def index_documents(self, chunks: List[DocumentChunk], append: bool = False):
        if not chunks:
            print("No chunks to index")
            return
        
        if append and self.chunks:
            existing_ids = {(c.source, c.chunk_id) for c in self.chunks}
            new_chunks = [c for c in chunks if (c.source, c.chunk_id) not in existing_ids]
            self.chunks = self.chunks + new_chunks
        else:
            self.chunks = chunks
        
        texts = [chunk.text for chunk in self.chunks]
        
        print(f"\nIndexing {len(self.chunks)} document chunks...")
        print("   Creating BM25 index...")

        tokenized_corpus = [text.split() for text in texts]
        self.bm25 = BM25Okapi(tokenized_corpus)

        print("   Generating embeddings...")

        self.chunk_embeddings = self.embedding_model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

        print(f"   Indexed {len(self.chunks)} chunks")
        print(f"   Embedding dimensions: {self.chunk_embeddings.shape[1]}")