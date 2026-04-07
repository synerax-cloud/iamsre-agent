"""
Authentication Middleware
JWT-based authentication
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.security import verify_token
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication middleware
    
    Skips authentication for public endpoints
    """
    
    # Public endpoints that don't require authentication
    PUBLIC_PATHS = [
        "/health",
        "/health/ready",
        "/health/live",
        "/metrics",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public paths
        if any(request.url.path.startswith(path) for path in self.PUBLIC_PATHS):
            return await call_next(request)
        
        # For development/demo, allow requests without auth
        # In production, enforce authentication
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            # TODO: In production, return 401
            # For now, allow unauthenticated access
            logger.debug("No auth header provided - allowing for development")
            request.state.user = None
            return await call_next(request)
        
        # Verify token
        try:
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid authorization header"}
                )
            
            token = auth_header.split(" ")[1]
            payload = verify_token(token)
            
            # Store user info in request state
            request.state.user = payload.get("sub")
            
        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or expired token"}
            )
        
        return await call_next(request)
