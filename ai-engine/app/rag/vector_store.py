"""
Vector store for RAG
Uses FAISS for local vector storage
"""

import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path

from app.core.config import settings
from app.core.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class VektorStore:
    """Vector store using FAISS"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.index = None
        self.documents = []
        self.metadata = []
        self.initialized = False
        
    async def initialize(self):
        """Initialize or load vector store"""
        if self.initialized:
            return
            
        store_path = Path(settings.VECTOR_DB_PATH)
        index_file = store_path / "faiss.index"
        docs_file = store_path / "documents.pkl"
        meta_file = store_path / "metadata.pkl"
        
        # Create directory if it doesn't exist
        store_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing index or create new
        if index_file.exists() and docs_file.exists():
            logger.info("Loading existing vector store...")
            self.index = faiss.read_index(str(index_file))
            with open(docs_file, 'rb') as f:
                self.documents = pickle.load(f)
            with open(meta_file, 'rb') as f:
                self.metadata = pickle.load(f)
            logger.info(f"Loaded {len(self.documents)} documents from vector store")
        else:
            logger.info("Creating new vector store...")
            # Create FAISS index (using L2 distance)
            self.index = faiss.IndexFlatL2(self.dimension)
            self.documents = []
            self.metadata = []
        
        self.initialized = True
    
    async def add_documents(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ):
        """Add documents to the vector store"""
        if not self.initialized:
            await self.initialize()
        
        # Generate embeddings
        llm_client = get_llm_client()
        embeddings = []
        
        for text in texts:
            embedding = await llm_client.embeddings(text)
            embeddings.append(embedding)
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Add to FAISS index
        self.index.add(embeddings_array)
        
        # Store documents and metadata
        self.documents.extend(texts)
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(texts))
        
        # Save to disk
        await self.save()
        
        logger.info(f"Added {len(texts)} documents to vector store")
    
    async def search(
        self,
        query: str,
        k: int = 5
    ) -> List[Tuple[str, Dict[str, Any], float]]:
        """Search for similar documents"""
        if not self.initialized:
            await self.initialize()
        
        if len(self.documents) == 0:
            return []
        
        # Generate query embedding
        llm_client = get_llm_client()
        query_embedding = await llm_client.embeddings(query)
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Search
        k = min(k, len(self.documents))
        distances, indices = self.index.search(query_array, k)
        
        # Format results
        results = []
        for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
            if idx < len(self.documents):
                results.append((
                    self.documents[idx],
                    self.metadata[idx],
                    float(dist)
                ))
        
        return results
    
    async def save(self):
        """Save vector store to disk"""
        store_path = Path(settings.VECTOR_DB_PATH)
        store_path.mkdir(parents=True, exist_ok=True)
        
        index_file = store_path / "faiss.index"
        docs_file = store_path / "documents.pkl"
        meta_file = store_path / "metadata.pkl"
        
        faiss.write_index(self.index, str(index_file))
        
        with open(docs_file, 'wb') as f:
            pickle.dump(self.documents, f)
        
        with open(meta_file, 'wb') as f:
            pickle.dump(self.metadata, f)
        
        logger.debug("Vector store saved to disk")
    
    async def clear(self):
        """Clear all documents from the vector store"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self.metadata = []
        await self.save()
        logger.info("Vector store cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            "total_documents": len(self.documents),
            "dimension": self.dimension,
            "index_size": self.index.ntotal if self.index else 0,
        }


# Global instance
_vector_store: Optional[VektorStore] = None


async def get_vector_store() -> VektorStore:
    """Get or create vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VektorStore(dimension=settings.EMBEDDING_DIMENSION)
        await _vector_store.initialize()
    return _vector_store
