"""
Chat Endpoints
Natural language interaction with the cluster
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.schemas import ChatRequest, ChatResponse
from app.core.config import settings
import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question about the cluster using natural language
    
    The AI engine will:
    1. Gather relevant context from collectors
    2. Use RAG to find similar past incidents
    3. Generate an intelligent response
    """
    try:
        # Call AI Engine
        async with httpx.AsyncClient() as client:
            ai_response = await client.post(
                f"{settings.AI_ENGINE_URL}/api/v1/query",
                json={"question": request.question, "context": request.context},
                timeout=30.0
            )
            ai_response.raise_for_status()
            ai_data = ai_response.json()
        
        # TODO: Store chat message in database
        
        return ChatResponse(
            answer=ai_data.get("answer", ""),
            confidence=ai_data.get("confidence", 0.0),
            sources=ai_data.get("sources", []),
            suggested_actions=ai_data.get("suggested_actions", []),
            timestamp=datetime.utcnow()
        )
        
    except httpx.HTTPError as e:
        logger.error(f"AI Engine request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Engine is unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in ask_question: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process question"
        )


@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get chat history"""
    # TODO: Implement database query for chat history
    return {
        "messages": [],
        "total": 0
    }
