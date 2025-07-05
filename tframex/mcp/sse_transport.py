# tframex/mcp/sse_transport.py
"""
SSE (Server-Sent Events) transport implementation for MCP.
Provides real-time server communication via SSE protocol.
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any, Callable, AsyncIterator
from dataclasses import dataclass
import aiohttp
from contextlib import asynccontextmanager

logger = logging.getLogger("tframex.mcp.sse_transport")


@dataclass
class SSEEvent:
    """Represents a Server-Sent Event."""
    event: Optional[str] = None
    data: Optional[str] = None
    id: Optional[str] = None
    retry: Optional[int] = None
    
    def is_valid(self) -> bool:
        """Check if event has data."""
        return self.data is not None


class SSEClient:
    """
    SSE client for MCP server communication.
    Handles connection, reconnection, and message parsing.
    """
    
    def __init__(self, url: str, 
                 headers: Optional[Dict[str, str]] = None,
                 timeout: int = 30,
                 reconnect_delay: int = 5,
                 max_reconnect_attempts: int = 3):
        """
        Initialize SSE client.
        
        Args:
            url: SSE endpoint URL
            headers: Additional headers (auth, etc.)
            timeout: Request timeout in seconds
            reconnect_delay: Delay between reconnection attempts
            max_reconnect_attempts: Maximum reconnection attempts
        """
        self.url = url
        self.headers = headers or {}
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._response: Optional[aiohttp.ClientResponse] = None
        self._last_event_id: Optional[str] = None
        self._reconnect_attempts = 0
        self._closed = False
    
    async def connect(self) -> None:
        """Establish SSE connection."""
        if self._session:
            await self.close()
        
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        
        # Add SSE-specific headers
        sse_headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            **self.headers
        }
        
        # Add Last-Event-ID for reconnection
        if self._last_event_id:
            sse_headers["Last-Event-ID"] = self._last_event_id
        
        try:
            self._response = await self._session.get(
                self.url,
                headers=sse_headers
            )
            self._response.raise_for_status()
            
            # Verify content type
            content_type = self._response.headers.get("Content-Type", "")
            if not content_type.startswith("text/event-stream"):
                raise ValueError(f"Invalid content type: {content_type}")
            
            self._reconnect_attempts = 0
            logger.info(f"SSE connected to {self.url}")
            
        except Exception as e:
            await self.close()
            raise ConnectionError(f"Failed to connect to SSE endpoint: {e}")
    
    async def close(self) -> None:
        """Close SSE connection."""
        self._closed = True
        
        if self._response:
            self._response.close()
            self._response = None
        
        if self._session:
            await self._session.close()
            self._session = None
        
        logger.info("SSE connection closed")
    
    async def events(self) -> AsyncIterator[SSEEvent]:
        """
        Iterate over SSE events with automatic reconnection.
        
        Yields:
            SSEEvent objects
        """
        while not self._closed:
            try:
                if not self._response:
                    await self._reconnect()
                
                async for event in self._parse_sse_stream():
                    if event.is_valid():
                        # Update last event ID for reconnection
                        if event.id:
                            self._last_event_id = event.id
                        
                        yield event
                
                # Stream ended normally, attempt reconnect
                if not self._closed:
                    logger.info("SSE stream ended, attempting reconnect")
                    await self._reconnect()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"SSE stream error: {e}")
                if not self._closed:
                    await self._reconnect()
    
    async def _parse_sse_stream(self) -> AsyncIterator[SSEEvent]:
        """Parse SSE events from response stream."""
        if not self._response:
            return
        
        event = SSEEvent()
        buffer = ""
        
        async for chunk in self._response.content:
            if self._closed:
                break
            
            # Decode chunk
            try:
                buffer += chunk.decode('utf-8')
            except UnicodeDecodeError:
                logger.warning("Failed to decode SSE chunk")
                continue
            
            # Process lines
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.rstrip('\r')
                
                if not line:  # Empty line signals end of event
                    if event.is_valid():
                        yield event
                    event = SSEEvent()
                    continue
                
                # Parse field
                if ':' in line:
                    field, value = line.split(':', 1)
                    value = value.lstrip()
                    
                    if field == 'event':
                        event.event = value
                    elif field == 'data':
                        if event.data is None:
                            event.data = value
                        else:
                            event.data += '\n' + value
                    elif field == 'id':
                        event.id = value
                    elif field == 'retry':
                        try:
                            event.retry = int(value)
                        except ValueError:
                            pass
                
                # Comment line (starts with :)
                elif line.startswith(':'):
                    pass  # Ignore comments
    
    async def _reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        if self._closed:
            return
        
        self._reconnect_attempts += 1
        
        if self._reconnect_attempts > self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) exceeded")
            raise ConnectionError("SSE reconnection failed")
        
        # Exponential backoff
        delay = self.reconnect_delay * (2 ** (self._reconnect_attempts - 1))
        logger.info(f"Reconnecting in {delay}s (attempt {self._reconnect_attempts})")
        
        await asyncio.sleep(delay)
        
        try:
            await self.connect()
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            raise


class MCPSSETransport:
    """
    MCP transport implementation using Server-Sent Events.
    Provides bidirectional communication over SSE + HTTP POST.
    """
    
    def __init__(self, base_url: str,
                 headers: Optional[Dict[str, str]] = None):
        """
        Initialize MCP SSE transport.
        
        Args:
            base_url: Base URL for the MCP server
            headers: Additional headers (auth, etc.)
        """
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        
        # SSE endpoint for server-to-client messages
        self.sse_url = f"{self.base_url}/sse"
        
        # HTTP endpoint for client-to-server messages
        self.rpc_url = f"{self.base_url}/rpc"
        
        self._sse_client: Optional[SSEClient] = None
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._read_task: Optional[asyncio.Task] = None
        self._write_queue: asyncio.Queue = asyncio.Queue()
        self._message_callback: Optional[Callable] = None
        self._closed = False
    
    @asynccontextmanager
    async def connect(self):
        """
        Connect to MCP server via SSE transport.
        
        Returns context manager that yields (read_stream, write_stream).
        """
        try:
            # Create HTTP session for sending messages
            self._http_session = aiohttp.ClientSession()
            
            # Create SSE client for receiving messages
            self._sse_client = SSEClient(
                self.sse_url,
                headers=self.headers
            )
            
            await self._sse_client.connect()
            
            # Create read/write stream adapters
            read_stream = SSEReadStream(self._sse_client)
            write_stream = SSEWriteStream(self._http_session, self.rpc_url, self.headers)
            
            yield read_stream, write_stream
            
        finally:
            await self.close()
    
    async def close(self) -> None:
        """Close all connections."""
        self._closed = True
        
        if self._sse_client:
            await self._sse_client.close()
            self._sse_client = None
        
        if self._http_session:
            await self._http_session.close()
            self._http_session = None


class SSEReadStream:
    """Adapter for reading MCP messages from SSE stream."""
    
    def __init__(self, sse_client: SSEClient):
        self._sse_client = sse_client
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start reading from SSE stream."""
        if not self._reader_task:
            self._reader_task = asyncio.create_task(self._read_loop())
    
    async def stop(self) -> None:
        """Stop reading from SSE stream."""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None
    
    async def _read_loop(self) -> None:
        """Read SSE events and convert to MCP messages."""
        try:
            async for event in self._sse_client.events():
                if event.event == "message" or not event.event:
                    try:
                        # Parse JSON-RPC message from event data
                        message = json.loads(event.data)
                        await self._message_queue.put(message)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse SSE message: {e}")
                
                elif event.event == "ping":
                    # Server keepalive
                    logger.debug("Received SSE ping")
                
                elif event.event == "error":
                    logger.error(f"SSE error event: {event.data}")
                    
        except Exception as e:
            logger.error(f"SSE read loop error: {e}", exc_info=True)
    
    async def receive(self) -> Dict[str, Any]:
        """Receive next MCP message."""
        # Start reader if needed
        if not self._reader_task:
            await self.start()
        
        return await self._message_queue.get()
    
    def at_eof(self) -> bool:
        """Check if stream is at EOF."""
        return self._sse_client._closed if self._sse_client else True


class SSEWriteStream:
    """Adapter for writing MCP messages via HTTP POST."""
    
    def __init__(self, session: aiohttp.ClientSession, 
                 rpc_url: str, headers: Dict[str, str]):
        self._session = session
        self._rpc_url = rpc_url
        self._headers = headers
    
    async def send(self, message: Dict[str, Any]) -> None:
        """Send MCP message via HTTP POST."""
        try:
            async with self._session.post(
                self._rpc_url,
                json=message,
                headers=self._headers
            ) as response:
                response.raise_for_status()
                
                # Some servers may return immediate responses
                if response.content_type == 'application/json':
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"Failed to send message via HTTP: {e}")
            raise


# Factory function for creating SSE transport
async def sse_client(base_url: str, headers: Optional[Dict[str, str]] = None):
    """
    Create an SSE transport client for MCP.
    
    Args:
        base_url: Base URL for the MCP server
        headers: Additional headers (auth, etc.)
        
    Returns:
        Context manager yielding (read_stream, write_stream)
    """
    transport = MCPSSETransport(base_url, headers)
    return transport.connect()