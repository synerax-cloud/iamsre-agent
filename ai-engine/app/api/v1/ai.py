"""
AI Engine API endpoints
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from app.rag.pipeline import get_rag_pipeline
from app.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class QueryRequest(BaseModel):
    question: str = Field(..., description="Question to ask")
    k: int = Field(5, description="Number of context documents to retrieve")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt")


class AnalyzeRequest(BaseModel):
    incident_description: str = Field(..., description="Incident description")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Metrics data")
    logs: Optional[List[str]] = Field(None, description="Log entries")


class RecommendRequest(BaseModel):
    cluster_state: Dict[str, Any] = Field(..., description="Current cluster state")
    issues: Optional[List[Dict[str, Any]]] = Field(None, description="Known issues")


class IngestRequest(BaseModel):
    documents: List[str] = Field(..., description="Documents to ingest")
    metadata: Optional[List[Dict[str, Any]]] = Field(None, description="Document metadata")


@router.post("/query", tags=["AI"])
async def query(request: QueryRequest):
    """Query the AI engine with RAG"""
    try:
        rag = await get_rag_pipeline()
        result = await rag.query(
            question=request.question,
            k=request.k,
            system_prompt=request.system_prompt
        )
        return result
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/analyze", tags=["AI"])
async def analyze_incident(request: AnalyzeRequest):
    """Analyze an incident and provide root cause analysis"""
    try:
        rag = await get_rag_pipeline()
        result = await rag.analyze_incident(
            incident_description=request.incident_description,
            metrics=request.metrics,
            logs=request.logs
        )
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/recommend", tags=["AI"])
async def generate_recommendations(request: RecommendRequest):
    """Generate recommendations based on cluster state"""
    try:
        rag = await get_rag_pipeline()
        recommendations = await rag.generate_recommendations(
            cluster_state=request.cluster_state,
            issues=request.issues
        )
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation generation failed: {str(e)}"
        )


@router.post("/ingest", tags=["Knowledge Base"])
async def ingest_documents(request: IngestRequest):
    """Ingest documents into the vector store"""
    try:
        vector_store = await get_vector_store()
        await vector_store.add_documents(
            texts=request.documents,
            metadata=request.metadata
        )
        return {
            "success": True,
            "message": f"Ingested {len(request.documents)} documents",
            "stats": vector_store.get_stats()
        }
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document ingestion failed: {str(e)}"
        )


@router.get("/knowledge-base/stats", tags=["Knowledge Base"])
async def get_knowledge_base_stats():
    """Get vector store statistics"""
    try:
        vector_store = await get_vector_store()
        return vector_store.get_stats()
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/knowledge-base/clear", tags=["Knowledge Base"])
async def clear_knowledge_base():
    """Clear all documents from the knowledge base"""
    try:
        vector_store = await get_vector_store()
        await vector_store.clear()
        return {
            "success": True,
            "message": "Knowledge base cleared"
        }
    except Exception as e:
        logger.error(f"Failed to clear knowledge base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
