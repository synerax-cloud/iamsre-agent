"""
RAG pipeline for context retrieval and augmented generation
"""

from typing import List, Dict, Any, Optional
import logging

from app.rag.vector_store import get_vector_store
from app.core.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline"""
    
    def __init__(self):
        self.llm_client = None
        self.vector_store = None
    
    async def initialize(self):
        """Initialize RAG pipeline"""
        self.llm_client = get_llm_client()
        self.vector_store = await get_vector_store()
    
    async def query(
        self,
        question: str,
        k: int = 5,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query with RAG
        
        Args:
            question: User question
            k: Number of context documents to retrieve
            system_prompt: Optional system prompt
            
        Returns:
            Response with answer and context
        """
        if not self.llm_client:
            await self.initialize()
        
        # Retrieve relevant context
        context_docs = await self.vector_store.search(question, k=k)
        
        # Build context string
        context_str = ""
        if context_docs:
            context_str = "\n\n".join([
                f"Document {i+1}:\n{doc}"
                for i, (doc, meta, score) in enumerate(context_docs)
            ])
        
        # Build prompt with context
        if context_str:
            prompt = f"""Context information:
{context_str}

Question: {question}

Please provide a detailed answer based on the context above. If the context doesn't contain relevant information, say so and provide your best general answer."""
        else:
            prompt = f"""Question: {question}

Please provide a detailed answer to this Kubernetes/SRE question."""
        
        # Generate response
        if not system_prompt:
            system_prompt = """You are an expert Kubernetes SRE assistant. You provide clear, actionable advice for troubleshooting and managing Kubernetes clusters. 
When answering questions:
1. Be specific and technical when needed
2. Provide step-by-step solutions
3. Explain the root cause when possible
4. Suggest preventive measures
5. Reference best practices"""
        
        response = await self.llm_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        
        return {
            "answer": response,
            "context_used": [
                {
                    "text": doc[:200] + "..." if len(doc) > 200 else doc,
                    "metadata": meta,
                    "relevance_score": float(score)
                }
                for doc, meta, score in context_docs
            ],
            "num_context_docs": len(context_docs)
        }
    
    async def analyze_incident(
        self,
        incident_description: str,
        metrics: Optional[Dict[str, Any]] = None,
        logs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze an incident and provide root cause analysis
        
        Args:
            incident_description: Description of the incident
            metrics: Optional metrics data
            logs: Optional log entries
            
        Returns:
            Analysis with root cause and recommendations
        """
        if not self.llm_client:
            await self.initialize()
        
        # Retrieve similar incidents from vector store
        similar_incidents = await self.vector_store.search(incident_description, k=3)
        
        # Build context
        context_parts = [f"Incident: {incident_description}"]
        
        if metrics:
            context_parts.append(f"\nMetrics:\n{self._format_metrics(metrics)}")
        
        if logs:
            context_parts.append(f"\nRecent Logs:\n" + "\n".join(logs[:10]))
        
        if similar_incidents:
            context_parts.append("\nSimilar Past Incidents:")
            for i, (doc, meta, score) in enumerate(similar_incidents[:2]):
                context_parts.append(f"{i+1}. {doc[:300]}")
        
        context = "\n".join(context_parts)
        
        # Generate analysis
        system_prompt = """You are an expert SRE analyzing a Kubernetes incident. Provide:
1. Root Cause Analysis: Identify the most likely cause
2. Impact Assessment: Describe the impact
3. Immediate Actions: Steps to resolve the incident
4. Preventive Measures: How to prevent recurrence
5. Related Issues: Any related problems to monitor

Be specific, technical, and actionable."""
        
        response = await self.llm_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this incident:\n\n{context}"}
            ]
        )
        
        return {
            "analysis": response,
            "similar_incidents": [
                {
                    "description": doc[:200],
                    "metadata": meta,
                    "similarity": float(score)
                }
                for doc, meta, score in similar_incidents
            ]
        }
    
    async def generate_recommendations(
        self,
        cluster_state: Dict[str, Any],
        issues: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on cluster state
        
        Args:
            cluster_state: Current cluster state
            issues: Optional list of known issues
            
        Returns:
            List of recommendations
        """
        if not self.llm_client:
            await self.initialize()
        
        # Build context
        context = f"Cluster State:\n{self._format_cluster_state(cluster_state)}"
        
        if issues:
            context += f"\n\nKnown Issues:\n"
            for i, issue in enumerate(issues):
                context += f"{i+1}. {issue.get('description', 'Unknown issue')}\n"
        
        # Generate recommendations
        system_prompt = """You are an expert SRE providing optimization recommendations for Kubernetes clusters.
For each recommendation, provide:
- Title: Brief description
- Priority: Critical/High/Medium/Low
- Action: Specific steps to implement
- Impact: Expected improvement
- Effort: Implementation complexity

Focus on actionable, specific recommendations."""
        
        response = await self.llm_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Provide recommendations for:\n\n{context}"}
            ]
        )
        
        # Parse response into structured recommendations
        # In a production system, you'd use structured output or parsing
        return [
            {
                "recommendation": response,
                "priority": "medium",
                "category": "optimization"
            }
        ]
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for context"""
        lines = []
        for key, value in metrics.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)
    
    def _format_cluster_state(self, state: Dict[str, Any]) -> str:
        """Format cluster state for context"""
        lines = []
        for key, value in state.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)


# Global instance
_rag_pipeline: Optional[RAGPipeline] = None


async def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline instance"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
        await _rag_pipeline.initialize()
    return _rag_pipeline
