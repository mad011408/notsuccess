"""NEXUS AI Agent - CLI Application"""

import asyncio
import sys
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class CLIConfig:
    """CLI configuration"""
    prompt: str = "nexus> "
    welcome_message: str = "Welcome to NEXUS AI Agent"
    exit_commands: List[str] = None
    history_file: str = ".nexus_history"
    enable_colors: bool = True

    def __post_init__(self):
        if self.exit_commands is None:
            self.exit_commands = ["exit", "quit", "q", "bye"]


class CLIInterface:
    """
    Command Line Interface for NEXUS Agent

    Features:
    - Interactive chat
    - Command handling
    - History support
    - Streaming responses
    """

    def __init__(
        self,
        agent=None,
        config: Optional[CLIConfig] = None
    ):
        self.agent = agent
        self.config = config or CLIConfig()
        self._running = False
        self._commands: Dict[str, callable] = {}
        self._history: List[str] = []

        self._register_default_commands()

    def _register_default_commands(self) -> None:
        """Register default commands"""
        self._commands = {
            "/help": self._cmd_help,
            "/clear": self._cmd_clear,
            "/history": self._cmd_history,
            "/state": self._cmd_state,
            "/reset": self._cmd_reset,
            "/tools": self._cmd_tools,
        }

    def register_command(self, name: str, handler: callable) -> None:
        """Register custom command"""
        self._commands[name] = handler

    async def run(self) -> None:
        """Run the CLI interface"""
        self._running = True
        self._print_welcome()

        while self._running:
            try:
                user_input = await self._get_input()

                if not user_input:
                    continue

                # Check for exit
                if user_input.lower() in self.config.exit_commands:
                    self._print("Goodbye!")
                    break

                # Check for commands
                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                    continue

                # Process with agent
                await self._process_input(user_input)

            except KeyboardInterrupt:
                self._print("\nUse 'exit' to quit")
            except EOFError:
                break
            except Exception as e:
                self._print(f"Error: {e}")

        self._running = False

    async def _get_input(self) -> str:
        """Get user input"""
        try:
            # Try to use readline for history
            import readline
            readline.read_history_file(self.config.history_file)
        except (ImportError, FileNotFoundError):
            pass

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: input(self.config.prompt)
        )

    async def _process_input(self, user_input: str) -> None:
        """Process user input with agent"""
        self._history.append(user_input)

        if not self.agent:
            self._print("Agent not initialized")
            return

        try:
            # Stream response
            self._print("")
            async for chunk in self.agent.run(user_input):
                print(chunk, end="", flush=True)
            print("\n")

        except Exception as e:
            self._print(f"Error: {e}")

    async def _handle_command(self, command: str) -> None:
        """Handle CLI command"""
        parts = command.split()
        cmd_name = parts[0]
        args = parts[1:]

        if cmd_name in self._commands:
            handler = self._commands[cmd_name]
            if asyncio.iscoroutinefunction(handler):
                await handler(*args)
            else:
                handler(*args)
        else:
            self._print(f"Unknown command: {cmd_name}")
            self._print("Type /help for available commands")

    def _print(self, message: str) -> None:
        """Print message with optional colors"""
        print(message)

    def _print_welcome(self) -> None:
        """Print welcome message"""
        self._print(f"\n{'=' * 50}")
        self._print(f"  {self.config.welcome_message}")
        self._print(f"{'=' * 50}")
        self._print("Type /help for available commands")
        self._print("Type 'exit' to quit\n")

    # Command handlers
    def _cmd_help(self, *args) -> None:
        """Show help"""
        self._print("\nAvailable commands:")
        self._print("  /help    - Show this help")
        self._print("  /clear   - Clear screen")
        self._print("  /history - Show command history")
        self._print("  /state   - Show agent state")
        self._print("  /reset   - Reset agent")
        self._print("  /tools   - List available tools")
        self._print("")

    def _cmd_clear(self, *args) -> None:
        """Clear screen"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def _cmd_history(self, *args) -> None:
        """Show history"""
        self._print("\nCommand history:")
        for i, cmd in enumerate(self._history[-20:], 1):
            self._print(f"  {i}. {cmd}")
        self._print("")

    def _cmd_state(self, *args) -> None:
        """Show agent state"""
        if self.agent:
            state = self.agent.get_state()
            self._print("\nAgent state:")
            for key, value in state.items():
                self._print(f"  {key}: {value}")
        else:
            self._print("Agent not initialized")

    def _cmd_reset(self, *args) -> None:
        """Reset agent"""
        if self.agent:
            self.agent.reset()
            self._print("Agent reset")
        else:
            self._print("Agent not initialized")

    def _cmd_tools(self, *args) -> None:
        """List tools"""
        if self.agent:
            tools = list(self.agent._tools.keys())
            self._print("\nAvailable tools:")
            for tool in tools:
                self._print(f"  - {tool}")
        else:
            self._print("Agent not initialized")

    def stop(self) -> None:
        """Stop the CLI"""
        self._running = False


def run_cli(agent=None) -> None:
    """Run CLI application"""
    cli = CLIInterface(agent=agent)
    asyncio.run(cli.run())


if __name__ == "__main__":
    run_cli()

