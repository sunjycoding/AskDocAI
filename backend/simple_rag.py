# simple_rag.py
import json
from typing import List, Dict

class SimplifiedRAG:
    """Simplified RAG without heavy dependencies"""
    
    def __init__(self):
        self.documents = {}
        print("Simplified RAG initialized")
    
    def index_document(self, doc_id: str, content: str, chunk_size: int = 500):
        """Store document chunks with simple indexing"""
        chunks = self._create_chunks(content, chunk_size)
        self.documents[doc_id] = {
            'chunks': chunks,
            'chunk_words': [set(chunk.lower().split()) for chunk in chunks]
        }
        print(f"Indexed {len(chunks)} chunks for document {doc_id[:8]}")
        return True
    
    def retrieve(self, doc_id: str, query: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant chunks using keyword matching"""
        if doc_id not in self.documents:
            return []
        
        doc_data = self.documents[doc_id]
        query_words = set(query.lower().split())
        
        # Score each chunk by word overlap
        chunk_scores = []
        for i, chunk_words in enumerate(doc_data['chunk_words']):
            score = len(query_words & chunk_words) / max(len(query_words), 1)
            chunk_scores.append((score, i))
        
        # Sort by score and get top chunks
        chunk_scores.sort(reverse=True)
        top_chunks = []
        for score, idx in chunk_scores[:top_k]:
            if score > 0:
                top_chunks.append(doc_data['chunks'][idx])
        
        return top_chunks if top_chunks else [doc_data['chunks'][0]]
    
    def _create_chunks(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks by word count"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - 50):  # 50 word overlap
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks if chunks else [text[:2000]]