"""NEXUS AI Agent - WebSocket Client"""

import asyncio
import json
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum


class WSState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    CLOSING = "closing"


@dataclass
class WSMessage:
    """WebSocket message"""
    data: Any
    type: str = "text"
    timestamp: float = 0.0


class WebSocketClient:
    """WebSocket client"""

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        heartbeat: float = 30.0,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 5
    ):
        self.url = url
        self.headers = headers or {}
        self.heartbeat = heartbeat
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts

        self._ws = None
        self._state = WSState.DISCONNECTED
        self._reconnect_attempts = 0
        self._callbacks: Dict[str, List[Callable]] = {
            'open': [],
            'message': [],
            'error': [],
            'close': [],
        }
        self._message_queue: List[WSMessage] = []

    @property
    def state(self) -> WSState:
        """Get connection state"""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._state == WSState.CONNECTED

    async def connect(self) -> bool:
        """Connect to WebSocket server"""
        import aiohttp

        if self._state == WSState.CONNECTED:
            return True

        self._state = WSState.CONNECTING

        try:
            session = aiohttp.ClientSession()
            self._ws = await session.ws_connect(
                self.url,
                headers=self.headers,
                heartbeat=self.heartbeat
            )
            self._state = WSState.CONNECTED
            self._reconnect_attempts = 0

            await self._trigger('open')

            # Start message handler
            asyncio.create_task(self._message_handler())

            return True

        except Exception as e:
            self._state = WSState.DISCONNECTED
            await self._trigger('error', str(e))
            return False

    async def disconnect(self) -> None:
        """Disconnect from server"""
        if self._ws:
            self._state = WSState.CLOSING
            await self._ws.close()
            self._ws = None
            self._state = WSState.DISCONNECTED
            await self._trigger('close')

    async def send(self, data: Any) -> bool:
        """
        Send message

        Args:
            data: Data to send (dict will be JSON encoded)

        Returns:
            Success status
        """
        if not self.is_connected:
            return False

        try:
            if isinstance(data, dict):
                await self._ws.send_json(data)
            elif isinstance(data, bytes):
                await self._ws.send_bytes(data)
            else:
                await self._ws.send_str(str(data))
            return True

        except Exception as e:
            await self._trigger('error', str(e))
            return False

    async def send_json(self, data: Dict[str, Any]) -> bool:
        """Send JSON message"""
        return await self.send(data)

    async def receive(self, timeout: Optional[float] = None) -> Optional[WSMessage]:
        """
        Receive message

        Args:
            timeout: Receive timeout

        Returns:
            WSMessage or None
        """
        if not self.is_connected:
            return None

        try:
            if timeout:
                msg = await asyncio.wait_for(
                    self._ws.receive(),
                    timeout=timeout
                )
            else:
                msg = await self._ws.receive()

            import time
            return WSMessage(
                data=msg.data,
                type=str(msg.type),
                timestamp=time.time()
            )

        except asyncio.TimeoutError:
            return None
        except Exception:
            return None

    async def _message_handler(self) -> None:
        """Handle incoming messages"""
        import aiohttp
        import time

        while self.is_connected:
            try:
                msg = await self._ws.receive()

                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.data
                    try:
                        data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        pass

                    ws_msg = WSMessage(
                        data=data,
                        type="text",
                        timestamp=time.time()
                    )
                    self._message_queue.append(ws_msg)
                    await self._trigger('message', ws_msg)

                elif msg.type == aiohttp.WSMsgType.BINARY:
                    ws_msg = WSMessage(
                        data=msg.data,
                        type="binary",
                        timestamp=time.time()
                    )
                    self._message_queue.append(ws_msg)
                    await self._trigger('message', ws_msg)

                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    self._state = WSState.DISCONNECTED
                    await self._trigger('close')

                    if self.auto_reconnect:
                        await self._reconnect()
                    break

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    await self._trigger('error', str(msg.data))
                    break

            except Exception as e:
                await self._trigger('error', str(e))
                break

    async def _reconnect(self) -> None:
        """Attempt to reconnect"""
        while self._reconnect_attempts < self.max_reconnect_attempts:
            self._reconnect_attempts += 1
            delay = min(30, 2 ** self._reconnect_attempts)

            await asyncio.sleep(delay)

            if await self.connect():
                return

        await self._trigger('error', "Max reconnection attempts reached")

    def on(self, event: str, callback: Callable) -> None:
        """
        Register event callback

        Args:
            event: Event name ('open', 'message', 'error', 'close')
            callback: Callback function
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def off(self, event: str, callback: Callable) -> None:
        """Remove event callback"""
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)

    async def _trigger(self, event: str, *args) -> None:
        """Trigger event callbacks"""
        for callback in self._callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    callback(*args)
            except Exception:
                pass

    def get_messages(self, clear: bool = True) -> List[WSMessage]:
        """Get queued messages"""
        messages = self._message_queue.copy()
        if clear:
            self._message_queue.clear()
        return messages

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

