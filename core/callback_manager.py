"""
NEXUS AI Agent - Callback Manager
"""

from typing import Optional, List, Dict, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import inspect

from config.logging_config import get_logger


logger = get_logger(__name__)


class CallbackEvent(str, Enum):
    """Standard callback events"""
    ON_START = "on_start"
    ON_END = "on_end"
    ON_ERROR = "on_error"
    ON_CHUNK = "on_chunk"
    ON_TOOL_START = "on_tool_start"
    ON_TOOL_END = "on_tool_end"
    ON_LLM_START = "on_llm_start"
    ON_LLM_END = "on_llm_end"
    ON_CHAIN_START = "on_chain_start"
    ON_CHAIN_END = "on_chain_end"
    ON_AGENT_ACTION = "on_agent_action"
    ON_AGENT_FINISH = "on_agent_finish"
    ON_RETRIEVER_START = "on_retriever_start"
    ON_RETRIEVER_END = "on_retriever_end"
    ON_COMPLETE = "on_complete"
    ON_SHUTDOWN = "on_shutdown"


@dataclass
class CallbackContext:
    """Context passed to callbacks"""
    event: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    run_id: Optional[str] = None


@dataclass
class CallbackRegistration:
    """Registration info for a callback"""
    callback: Callable
    event: str
    priority: int = 0
    once: bool = False
    filter_fn: Optional[Callable[[CallbackContext], bool]] = None


class CallbackManager:
    """
    Manages callbacks throughout the agent lifecycle

    Handles:
    - Callback registration
    - Event triggering
    - Async callback execution
    - Callback filtering
    """

    def __init__(self):
        self._callbacks: Dict[str, List[CallbackRegistration]] = {}
        self._global_callbacks: List[CallbackRegistration] = []
        self._fired_once: Set[int] = set()
        self._enabled = True

    def add(
        self,
        event: str,
        callback: Callable,
        priority: int = 0,
        once: bool = False,
        filter_fn: Optional[Callable[[CallbackContext], bool]] = None
    ) -> int:
        """
        Add a callback for an event

        Args:
            event: Event name
            callback: Callback function
            priority: Execution priority (higher = first)
            once: If True, callback fires only once
            filter_fn: Optional filter function

        Returns:
            Registration ID
        """
        registration = CallbackRegistration(
            callback=callback,
            event=event,
            priority=priority,
            once=once,
            filter_fn=filter_fn
        )

        if event not in self._callbacks:
            self._callbacks[event] = []

        self._callbacks[event].append(registration)
        self._callbacks[event].sort(key=lambda x: x.priority, reverse=True)

        registration_id = id(registration)
        logger.debug(f"Callback registered for event: {event}")

        return registration_id

    def add_global(
        self,
        callback: Callable,
        priority: int = 0
    ) -> int:
        """Add a global callback that fires on all events"""
        registration = CallbackRegistration(
            callback=callback,
            event="*",
            priority=priority
        )

        self._global_callbacks.append(registration)
        self._global_callbacks.sort(key=lambda x: x.priority, reverse=True)

        return id(registration)

    def remove(self, event: str, callback: Callable) -> bool:
        """Remove a callback"""
        if event not in self._callbacks:
            return False

        original_length = len(self._callbacks[event])
        self._callbacks[event] = [
            r for r in self._callbacks[event]
            if r.callback != callback
        ]

        return len(self._callbacks[event]) < original_length

    def remove_by_id(self, registration_id: int) -> bool:
        """Remove callback by registration ID"""
        for event, registrations in self._callbacks.items():
            for reg in registrations:
                if id(reg) == registration_id:
                    registrations.remove(reg)
                    return True

        for reg in self._global_callbacks:
            if id(reg) == registration_id:
                self._global_callbacks.remove(reg)
                return True

        return False

    async def trigger(
        self,
        event: str,
        **kwargs
    ) -> List[Any]:
        """
        Trigger callbacks for an event

        Args:
            event: Event name
            **kwargs: Data to pass to callbacks

        Returns:
            List of callback results
        """
        if not self._enabled:
            return []

        context = CallbackContext(
            event=event,
            data=kwargs
        )

        results = []
        callbacks_to_run = []

        # Collect event-specific callbacks
        if event in self._callbacks:
            callbacks_to_run.extend(self._callbacks[event])

        # Add global callbacks
        callbacks_to_run.extend(self._global_callbacks)

        # Sort by priority
        callbacks_to_run.sort(key=lambda x: x.priority, reverse=True)

        for registration in callbacks_to_run:
            # Check if once callback already fired
            if registration.once and id(registration) in self._fired_once:
                continue

            # Apply filter
            if registration.filter_fn and not registration.filter_fn(context):
                continue

            try:
                result = await self._execute_callback(registration.callback, context)
                results.append(result)

                # Mark once callbacks as fired
                if registration.once:
                    self._fired_once.add(id(registration))

            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")
                # Don't let one callback error stop others

        return results

    async def _execute_callback(
        self,
        callback: Callable,
        context: CallbackContext
    ) -> Any:
        """Execute a single callback"""
        # Check if callback accepts context
        sig = inspect.signature(callback)
        params = list(sig.parameters.keys())

        if asyncio.iscoroutinefunction(callback):
            if params:
                return await callback(context)
            return await callback()
        else:
            if params:
                return callback(context)
            return callback()

    def on(self, event: str):
        """Decorator for adding callbacks"""
        def decorator(func: Callable) -> Callable:
            self.add(event, func)
            return func
        return decorator

    def once(self, event: str):
        """Decorator for one-time callbacks"""
        def decorator(func: Callable) -> Callable:
            self.add(event, func, once=True)
            return func
        return decorator

    def enable(self) -> None:
        """Enable callbacks"""
        self._enabled = True

    def disable(self) -> None:
        """Disable callbacks"""
        self._enabled = False

    def clear(self, event: Optional[str] = None) -> None:
        """Clear callbacks"""
        if event:
            self._callbacks.pop(event, None)
        else:
            self._callbacks.clear()
            self._global_callbacks.clear()
            self._fired_once.clear()

    def get_events(self) -> List[str]:
        """Get list of events with registered callbacks"""
        return list(self._callbacks.keys())

    def get_callback_count(self, event: Optional[str] = None) -> int:
        """Get number of registered callbacks"""
        if event:
            return len(self._callbacks.get(event, []))
        return sum(len(cbs) for cbs in self._callbacks.values()) + len(self._global_callbacks)


class CallbackHandler:
    """Base class for callback handlers"""

    def __init__(self):
        self._manager: Optional[CallbackManager] = None

    def bind(self, manager: CallbackManager) -> None:
        """Bind to a callback manager"""
        self._manager = manager
        self._register_callbacks()

    def _register_callbacks(self) -> None:
        """Register all callbacks - override in subclass"""
        pass

    async def on_start(self, context: CallbackContext) -> None:
        """Called when processing starts"""
        pass

    async def on_end(self, context: CallbackContext) -> None:
        """Called when processing ends"""
        pass

    async def on_error(self, context: CallbackContext) -> None:
        """Called on error"""
        pass

    async def on_llm_start(self, context: CallbackContext) -> None:
        """Called when LLM call starts"""
        pass

    async def on_llm_end(self, context: CallbackContext) -> None:
        """Called when LLM call ends"""
        pass

    async def on_tool_start(self, context: CallbackContext) -> None:
        """Called when tool execution starts"""
        pass

    async def on_tool_end(self, context: CallbackContext) -> None:
        """Called when tool execution ends"""
        pass


class LoggingCallbackHandler(CallbackHandler):
    """Callback handler that logs all events"""

    def _register_callbacks(self) -> None:
        if not self._manager:
            return

        for event in CallbackEvent:
            self._manager.add(event.value, self._log_event)

    async def _log_event(self, context: CallbackContext) -> None:
        """Log event"""
        logger.info(f"Event: {context.event} - Data: {context.data}")


class MetricsCallbackHandler(CallbackHandler):
    """Callback handler that collects metrics"""

    def __init__(self):
        super().__init__()
        self.metrics: Dict[str, Any] = {
            "events": {},
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0,
            "total_latency_ms": 0
        }

    def _register_callbacks(self) -> None:
        if not self._manager:
            return

        self._manager.add(CallbackEvent.ON_LLM_END.value, self._on_llm_end)
        self._manager.add(CallbackEvent.ON_TOOL_END.value, self._on_tool_end)
        self._manager.add(CallbackEvent.ON_ERROR.value, self._on_error)

    async def _on_llm_end(self, context: CallbackContext) -> None:
        self.metrics["llm_calls"] += 1
        if "latency_ms" in context.data:
            self.metrics["total_latency_ms"] += context.data["latency_ms"]

    async def _on_tool_end(self, context: CallbackContext) -> None:
        self.metrics["tool_calls"] += 1

    async def _on_error(self, context: CallbackContext) -> None:
        self.metrics["errors"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.copy()

    def reset_metrics(self) -> None:
        self.metrics = {
            "events": {},
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0,
            "total_latency_ms": 0
        }
