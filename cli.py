"""
NEXUS AI Agent - CLI Entry Point
"""

import asyncio
import click
from typing import Optional

from config.settings import get_settings
from config.logging_config import setup_logging, get_logger
from core.nexus_agent import create_agent
from interfaces.cli import CLIInterface


logger = get_logger(__name__)


@click.group()
@click.version_option(version="1.0.0", prog_name="nexus")
def cli():
    """NEXUS AI Agent - Command Line Interface"""
    pass


@cli.command()
@click.argument("task")
@click.option("--model", "-m", default="claude-opus-4-5", help="LLM model to use")
@click.option("--no-stream", is_flag=True, help="Disable streaming")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(task: str, model: str, no_stream: bool, verbose: bool):
    """Run a single task"""
    setup_logging("DEBUG" if verbose else "INFO")

    async def execute():
        agent = create_agent(model=model)

        try:
            if no_stream:
                response = await agent.chat(task)
                click.echo(response)
            else:
                async for chunk in agent.run(task, stream=True):
                    click.echo(chunk, nl=False)
                click.echo()
        finally:
            await agent.shutdown()

    asyncio.run(execute())


@cli.command()
@click.option("--model", "-m", default="claude-opus-4-5", help="LLM model to use")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def chat(model: str, verbose: bool):
    """Start interactive chat session"""
    setup_logging("DEBUG" if verbose else "INFO")

    async def run_chat():
        agent = create_agent(model=model)
        interface = CLIInterface(agent=agent)
        await interface.run()

    asyncio.run(run_chat())


@cli.command()
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", "-p", default=8000, type=int, help="Server port")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the API server"""
    setup_logging()
    click.echo(f"Starting server on {host}:{port}")

    import uvicorn
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload
    )


@cli.command()
def info():
    """Show configuration info"""
    settings = get_settings()

    click.echo("\n=== NEXUS AI Agent Configuration ===\n")
    click.echo(f"App Name: {settings.app_name}")
    click.echo(f"Default Provider: {settings.default_llm_provider}")
    click.echo(f"Default Model: {settings.default_model}")
    click.echo(f"Temperature: {settings.default_temperature}")
    click.echo(f"Max Tokens: {settings.max_tokens}")
    click.echo(f"Timeout: {settings.default_timeout}s")
    click.echo(f"Debug Mode: {settings.debug}")
    click.echo()


@cli.command()
@click.argument("provider", type=click.Choice(["openai", "anthropic", "google", "mistral", "groq"]))
@click.argument("api_key")
def configure(provider: str, api_key: str):
    """Configure API keys"""
    import os

    env_vars = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "groq": "GROQ_API_KEY",
    }

    env_var = env_vars.get(provider)
    if env_var:
        # Write to .env file
        env_file = ".env"
        lines = []

        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                lines = f.readlines()

        # Update or add the key
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{env_var}="):
                lines[i] = f"{env_var}={api_key}\n"
                found = True
                break

        if not found:
            lines.append(f"{env_var}={api_key}\n")

        with open(env_file, "w") as f:
            f.writelines(lines)

        click.echo(f"✓ {provider} API key configured")
    else:
        click.echo(f"Unknown provider: {provider}")


@cli.command("list-models")
def list_models():
    """List available models"""
    models = {
        "OpenAI": ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
        "Anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "Google": ["gemini-pro", "gemini-ultra"],
        "Mistral": ["mistral-large", "mistral-medium", "mistral-small"],
        "Groq": ["llama3-70b", "llama3-8b", "mixtral-8x7b"],
    }

    click.echo("\n=== Available Models ===\n")
    for provider, model_list in models.items():
        click.echo(f"{provider}:")
        for model in model_list:
            click.echo(f"  - {model}")
    click.echo()


if __name__ == "__main__":
    cli()

