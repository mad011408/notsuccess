"""NEXUS AI Agent - API Models"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    stream: bool = Field(False, description="Enable streaming response")


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str = Field(..., description="Agent response")
    session_id: Optional[str] = Field(None, description="Session ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentRequest(BaseModel):
    """Agent task request"""
    task: str = Field(..., description="Task description")
    tools: Optional[List[str]] = Field(None, description="Tools to use")
    max_iterations: Optional[int] = Field(10, description="Max iterations")
    context: Optional[Dict[str, Any]] = Field(None, description="Task context")


class AgentResponse(BaseModel):
    """Agent task response"""
    success: bool = Field(..., description="Task success status")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message")
    iterations: int = Field(0, description="Iterations used")
    duration: float = Field(0.0, description="Duration in seconds")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    code: Optional[int] = Field(None, description="Error code")


class ToolSchema(BaseModel):
    """Tool schema model"""
    name: str
    description: str
    parameters: Dict[str, Any]


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    created_at: datetime
    message_count: int
    last_activity: datetime


class CompletionRequest(BaseModel):
    """Completion request (OpenAI-compatible)"""
    model: str = Field("gpt-4o", description="Model to use")
    messages: List[Dict[str, str]] = Field(..., description="Messages")
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1)
    stream: bool = Field(False)
    stop: Optional[List[str]] = Field(None)


class CompletionResponse(BaseModel):
    """Completion response (OpenAI-compatible)"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class EmbeddingRequest(BaseModel):
    """Embedding request"""
    input: str = Field(..., description="Text to embed")
    model: str = Field("text-embedding-ada-002", description="Embedding model")


class EmbeddingResponse(BaseModel):
    """Embedding response"""
    embedding: List[float]
    model: str
    usage: Dict[str, int]

