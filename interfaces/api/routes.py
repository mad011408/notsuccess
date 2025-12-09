"""NEXUS AI Agent - API Routes"""

from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio

from .models import (
    ChatRequest,
    ChatResponse,
    AgentRequest,
    AgentResponse,
    HealthResponse,
    ErrorResponse
)
from config.logging_config import get_logger


logger = get_logger(__name__)


def create_api_app(
    agent=None,
    title: str = "NEXUS AI Agent API",
    version: str = "1.0.0"
) -> FastAPI:
    """
    Create FastAPI application

    Args:
        agent: NexusAgent instance
        title: API title
        version: API version

    Returns:
        FastAPI application
    """
    app = FastAPI(
        title=title,
        version=version,
        description="NEXUS AI Agent REST API"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store agent reference
    app.state.agent = agent

    # Health check
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        return HealthResponse(
            status="healthy",
            version=version
        )

    # Chat endpoint
    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        if not app.state.agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        try:
            response = await app.state.agent.chat(request.message)
            return ChatResponse(
                message=response,
                session_id=request.session_id
            )
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Streaming chat endpoint
    @app.post("/chat/stream")
    async def chat_stream(request: ChatRequest):
        if not app.state.agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        async def generate():
            try:
                async for chunk in app.state.agent.run(request.message):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: [ERROR] {str(e)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )

    # Agent task endpoint
    @app.post("/agent/run", response_model=AgentResponse)
    async def run_agent(request: AgentRequest):
        if not app.state.agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        try:
            result = await app.state.agent.execute_task(
                task=request.task,
                tools=request.tools,
                max_iterations=request.max_iterations
            )
            return AgentResponse(
                success=True,
                result=result
            )
        except Exception as e:
            logger.error(f"Agent error: {e}")
            return AgentResponse(
                success=False,
                error=str(e)
            )

    # Get agent state
    @app.get("/agent/state")
    async def get_agent_state():
        if not app.state.agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        return app.state.agent.get_state()

    # Reset agent
    @app.post("/agent/reset")
    async def reset_agent():
        if not app.state.agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        app.state.agent.reset()
        return {"status": "reset"}

    # List tools
    @app.get("/tools")
    async def list_tools():
        if not app.state.agent:
            return {"tools": []}

        return {
            "tools": list(app.state.agent._tools.keys())
        }

    return app


def create_api_router():
    """Create API router for modular inclusion"""
    from fastapi import APIRouter

    router = APIRouter(prefix="/api/v1")

    @router.get("/status")
    async def status():
        return {"status": "ok"}

    return router

