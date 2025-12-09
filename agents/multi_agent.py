"""NEXUS AI Agent - Multi-Agent System"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from config.logging_config import get_logger
from .base_agent import BaseAgent, AgentOutput, AgentContext


logger = get_logger(__name__)


class CommunicationMode(str, Enum):
    """Agent communication modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    COLLABORATIVE = "collaborative"


@dataclass
class Message:
    """Inter-agent message"""
    sender: str
    receiver: str
    content: str
    message_type: str = "text"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TeamResult:
    """Result from team execution"""
    task: str
    results: List[AgentOutput]
    messages: List[Message]
    success: bool
    error: Optional[str] = None
    total_time: float = 0.0


class AgentTeam:
    """
    Team of agents working together

    Coordinates multiple agents on complex tasks
    """

    def __init__(
        self,
        name: str = "Team",
        mode: CommunicationMode = CommunicationMode.SEQUENTIAL
    ):
        self.name = name
        self.mode = mode
        self._agents: Dict[str, BaseAgent] = {}
        self._roles: Dict[str, str] = {}
        self._messages: List[Message] = []
        self._coordinator: Optional[BaseAgent] = None

    def add_agent(self, agent: BaseAgent, role: str = "") -> None:
        """
        Add agent to team

        Args:
            agent: Agent to add
            role: Optional role description
        """
        self._agents[agent.id] = agent
        self._roles[agent.id] = role or agent.name
        logger.info(f"Agent added to team: {agent.name} as {role}")

    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent from team"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            del self._roles[agent_id]
            return True
        return False

    def set_coordinator(self, agent: BaseAgent) -> None:
        """Set team coordinator"""
        self._coordinator = agent
        if agent.id not in self._agents:
            self.add_agent(agent, "coordinator")

    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TeamResult:
        """
        Run team on task

        Args:
            task: Task to execute
            context: Optional context

        Returns:
            TeamResult
        """
        import time
        start_time = time.time()

        self._messages.clear()
        results = []

        try:
            if self.mode == CommunicationMode.SEQUENTIAL:
                results = await self._run_sequential(task, context)
            elif self.mode == CommunicationMode.PARALLEL:
                results = await self._run_parallel(task, context)
            elif self.mode == CommunicationMode.HIERARCHICAL:
                results = await self._run_hierarchical(task, context)
            elif self.mode == CommunicationMode.COLLABORATIVE:
                results = await self._run_collaborative(task, context)

            return TeamResult(
                task=task,
                results=results,
                messages=self._messages.copy(),
                success=all(r.success for r in results),
                total_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Team execution error: {e}")
            return TeamResult(
                task=task,
                results=results,
                messages=self._messages.copy(),
                success=False,
                error=str(e),
                total_time=time.time() - start_time
            )

    async def _run_sequential(
        self,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[AgentOutput]:
        """Run agents sequentially"""
        results = []
        current_context = context or {}

        for agent in self._agents.values():
            # Include previous results in context
            agent_context = AgentContext(
                task=task,
                variables={**current_context, "previous_results": results}
            )

            result = await agent.run(task, agent_context)
            results.append(result)

            # Pass result to next agent
            current_context["last_result"] = result.content

            self._add_message(Message(
                sender=agent.id,
                receiver="team",
                content=result.content[:500],
                message_type="result"
            ))

        return results

    async def _run_parallel(
        self,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[AgentOutput]:
        """Run agents in parallel"""
        agent_context = AgentContext(
            task=task,
            variables=context or {}
        )

        tasks = [
            agent.run(task, agent_context)
            for agent in self._agents.values()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(AgentOutput(
                    content="",
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results

    async def _run_hierarchical(
        self,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[AgentOutput]:
        """Run with coordinator delegating to workers"""
        if not self._coordinator:
            return await self._run_sequential(task, context)

        results = []

        # Coordinator plans the work
        plan_context = AgentContext(
            task=f"Plan this task and identify subtasks: {task}",
            variables=context or {}
        )
        plan_result = await self._coordinator.run(task, plan_context)
        results.append(plan_result)

        # Workers execute
        worker_agents = [a for a in self._agents.values() if a.id != self._coordinator.id]
        if worker_agents:
            worker_results = await asyncio.gather(*[
                agent.run(task, AgentContext(task=task))
                for agent in worker_agents
            ])
            results.extend(worker_results)

        # Coordinator synthesizes
        synthesis_context = AgentContext(
            task=f"Synthesize results for: {task}",
            variables={"worker_results": [r.content for r in results[1:]]}
        )
        synthesis_result = await self._coordinator.run(
            "Synthesize the results",
            synthesis_context
        )
        results.append(synthesis_result)

        return results

    async def _run_collaborative(
        self,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[AgentOutput]:
        """Run with agents collaborating"""
        results = []
        shared_context = context or {}
        iterations = 3

        for i in range(iterations):
            for agent in self._agents.values():
                agent_context = AgentContext(
                    task=task,
                    variables={
                        **shared_context,
                        "iteration": i,
                        "team_results": [r.content for r in results]
                    }
                )

                result = await agent.run(task, agent_context)
                results.append(result)

                # Broadcast to other agents
                self._add_message(Message(
                    sender=agent.id,
                    receiver="all",
                    content=result.content[:500],
                    message_type="contribution"
                ))

        return results

    def _add_message(self, message: Message) -> None:
        """Add message to history"""
        self._messages.append(message)

    def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        content: str
    ) -> bool:
        """Send message between agents"""
        if sender_id not in self._agents:
            return False

        self._add_message(Message(
            sender=sender_id,
            receiver=receiver_id,
            content=content
        ))
        return True

    def get_messages(
        self,
        agent_id: Optional[str] = None
    ) -> List[Message]:
        """Get messages, optionally filtered by agent"""
        if agent_id:
            return [
                m for m in self._messages
                if m.sender == agent_id or m.receiver in [agent_id, "all"]
            ]
        return self._messages.copy()

    def get_agents(self) -> List[Dict[str, Any]]:
        """Get team agents info"""
        return [
            {**agent.get_info(), "role": self._roles[agent.id]}
            for agent in self._agents.values()
        ]


class MultiAgentSystem:
    """
    Multi-agent orchestration system

    Manages multiple teams and complex workflows
    """

    def __init__(self):
        self._teams: Dict[str, AgentTeam] = {}
        self._workflows: Dict[str, List[str]] = {}

    def create_team(
        self,
        name: str,
        mode: CommunicationMode = CommunicationMode.SEQUENTIAL
    ) -> AgentTeam:
        """Create a new team"""
        team = AgentTeam(name=name, mode=mode)
        self._teams[name] = team
        return team

    def get_team(self, name: str) -> Optional[AgentTeam]:
        """Get team by name"""
        return self._teams.get(name)

    def remove_team(self, name: str) -> bool:
        """Remove team"""
        if name in self._teams:
            del self._teams[name]
            return True
        return False

    def create_workflow(self, name: str, team_sequence: List[str]) -> None:
        """Create workflow of teams"""
        self._workflows[name] = team_sequence

    async def run_workflow(
        self,
        workflow_name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[TeamResult]:
        """Run a workflow"""
        if workflow_name not in self._workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        results = []
        current_context = context or {}

        for team_name in self._workflows[workflow_name]:
            team = self._teams.get(team_name)
            if not team:
                continue

            result = await team.run(task, current_context)
            results.append(result)

            # Pass results to next team
            current_context["previous_team_results"] = [
                r.content for r in result.results
            ]

        return results

    async def run_team(
        self,
        team_name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[TeamResult]:
        """Run a specific team"""
        team = self._teams.get(team_name)
        if not team:
            return None
        return await team.run(task, context)

    def list_teams(self) -> List[str]:
        """List team names"""
        return list(self._teams.keys())

    def list_workflows(self) -> List[str]:
        """List workflow names"""
        return list(self._workflows.keys())

