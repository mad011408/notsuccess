"""
NEXUS AI Agent - FastAPI Application
"""

import uvicorn
from typing import Optional

from config.settings import get_settings
from config.logging_config import setup_logging, get_logger
from interfaces.api import create_api_app
from core.nexus_agent import create_agent


logger = get_logger(__name__)


def create_app():
    """Create FastAPI application"""
    settings = get_settings()

    # Create agent
    agent = create_agent(
        model=settings.default_model,
        temperature=settings.default_temperature
    )

    # Create API app
    app = create_api_app(
        agent=agent,
        title="NEXUS AI Agent API",
        version="1.0.0"
    )

    return app


# Create app instance
app = create_app()


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False
):
    """Run the API server"""
    setup_logging()
    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NEXUS AI Agent API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    run_server(host=args.host, port=args.port, reload=args.reload)

