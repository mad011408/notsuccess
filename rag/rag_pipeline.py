"""NEXUS AI Agent - RAG Pipeline"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class RAGResult:
    """RAG query result"""
    query: str
    answer: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    context: str = ""
    confidence: float = 0.0


@dataclass
class RAGConfig:
    """RAG pipeline configuration"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    rerank: bool = True
    min_relevance: float = 0.5


class RAGPipeline:
    """
    Retrieval-Augmented Generation Pipeline

    Components:
    - Document loading and processing
    - Text splitting and chunking
    - Embedding and indexing
    - Retrieval
    - Optional reranking
    - LLM generation
    """

    def __init__(
        self,
        vector_store=None,
        embedder=None,
        llm_client=None,
        config: Optional[RAGConfig] = None
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm_client = llm_client
        self.config = config or RAGConfig()

        self._documents: List[Dict[str, Any]] = []
        self._index_built = False

        logger.info("RAG Pipeline initialized")

    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        Add documents to the pipeline

        Args:
            documents: List of documents with 'content' and optional 'metadata'
            batch_size: Batch size for processing

        Returns:
            Number of documents added
        """
        from .text_splitter import TextSplitter

        splitter = TextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )

        chunks = []
        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            # Split into chunks
            doc_chunks = splitter.split(content)
            for i, chunk in enumerate(doc_chunks):
                chunks.append({
                    "content": chunk,
                    "metadata": {**metadata, "chunk_index": i}
                })

        # Embed and store
        if self.embedder and self.vector_store:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]

                # Get embeddings
                texts = [c["content"] for c in batch]
                embeddings = await self.embedder.embed_batch(texts)

                # Store in vector store
                for chunk, embedding in zip(batch, embeddings):
                    await self.vector_store.add(
                        content=chunk["content"],
                        embedding=embedding,
                        metadata=chunk["metadata"]
                    )

        self._documents.extend(chunks)
        self._index_built = True

        logger.info(f"Added {len(chunks)} chunks from {len(documents)} documents")
        return len(chunks)

    async def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> RAGResult:
        """
        Query the RAG pipeline

        Args:
            query: User query
            top_k: Number of results to retrieve
            filter_metadata: Optional metadata filter

        Returns:
            RAGResult with answer and sources
        """
        top_k = top_k or self.config.top_k
        result = RAGResult(query=query)

        try:
            # Retrieve relevant documents
            retrieved = await self._retrieve(query, top_k, filter_metadata)

            if not retrieved:
                result.answer = "No relevant information found."
                return result

            # Optionally rerank
            if self.config.rerank:
                retrieved = await self._rerank(query, retrieved)

            # Build context
            context = self._build_context(retrieved)
            result.context = context
            result.sources = retrieved

            # Generate answer
            result.answer = await self._generate(query, context)

            # Estimate confidence
            result.confidence = self._estimate_confidence(retrieved)

        except Exception as e:
            logger.error(f"RAG query error: {e}")
            result.answer = f"Error processing query: {e}"

        return result

    async def _retrieve(
        self,
        query: str,
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents"""
        if not self.vector_store or not self.embedder:
            return []

        # Get query embedding
        query_embedding = await self.embedder.embed(query)

        # Search vector store
        results = await self.vector_store.search(
            embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )

        # Filter by relevance threshold
        filtered = [
            r for r in results
            if r.get("score", 0) >= self.config.min_relevance
        ]

        return filtered

    async def _rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rerank retrieved documents"""
        from .reranker import Reranker

        reranker = Reranker()
        return await reranker.rerank(query, documents)

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context from retrieved documents"""
        context_parts = []

        for i, doc in enumerate(documents, 1):
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("source", f"Document {i}")
            context_parts.append(f"[{source}]\n{content}")

        return "\n\n---\n\n".join(context_parts)

    async def _generate(self, query: str, context: str) -> str:
        """Generate answer using LLM"""
        if not self.llm_client:
            return "LLM not available for generation."

        prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {query}

Instructions:
- Answer based only on the provided context
- If the context doesn't contain the answer, say so
- Be concise and accurate
- Cite sources when possible

Answer:"""

        response = await self.llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.content

    def _estimate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """Estimate answer confidence based on retrieval scores"""
        if not documents:
            return 0.0

        scores = [d.get("score", 0) for d in documents]
        avg_score = sum(scores) / len(scores)

        return min(1.0, avg_score)

    async def delete_documents(
        self,
        filter_metadata: Dict[str, Any]
    ) -> int:
        """Delete documents matching metadata filter"""
        if self.vector_store:
            return await self.vector_store.delete(filter_metadata)
        return 0

    def clear(self) -> None:
        """Clear all documents"""
        self._documents.clear()
        if self.vector_store:
            self.vector_store.clear()
        self._index_built = False

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return {
            "total_chunks": len(self._documents),
            "index_built": self._index_built,
            "config": {
                "chunk_size": self.config.chunk_size,
                "chunk_overlap": self.config.chunk_overlap,
                "top_k": self.config.top_k,
                "rerank": self.config.rerank
            }
        }

