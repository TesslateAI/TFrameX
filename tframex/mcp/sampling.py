# tframex/mcp/sampling.py
"""
MCP Sampling implementation for TFrameX.
Provides server-initiated LLM sampling with human-in-the-loop approval.
"""
import asyncio
import logging
from typing import List, Dict, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

from tframex.models.primitives import Message as TFrameXMessage
from tframex.util.llms import BaseLLMWrapper

logger = logging.getLogger("tframex.mcp.sampling")


class SamplingApprovalStatus(Enum):
    """Status of a sampling request approval."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    MODIFIED = "modified"  # User modified before approval


@dataclass
class ModelPreferences:
    """Model selection preferences for sampling."""
    hints: List[Dict[str, str]] = field(default_factory=list)  # Model name hints
    cost_priority: float = 0.5  # 0-1, higher = prefer cheaper
    speed_priority: float = 0.5  # 0-1, higher = prefer faster
    intelligence_priority: float = 0.5  # 0-1, higher = prefer smarter
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP-compatible dictionary."""
        return {
            "hints": self.hints,
            "costPriority": self.cost_priority,
            "speedPriority": self.speed_priority,
            "intelligencePriority": self.intelligence_priority
        }


@dataclass 
class SamplingMessage:
    """Message in a sampling request."""
    role: str  # "user", "assistant", "system"
    content: Union[str, Dict[str, Any]]  # Text or multi-modal content
    
    @classmethod
    def from_mcp(cls, mcp_msg: Dict[str, Any]) -> "SamplingMessage":
        """Create from MCP message format."""
        return cls(
            role=mcp_msg["role"],
            content=mcp_msg["content"]
        )
    
    def to_tframex_message(self) -> TFrameXMessage:
        """Convert to TFrameX Message format."""
        if isinstance(self.content, str):
            return TFrameXMessage(role=self.role, content=self.content)
        elif isinstance(self.content, dict):
            # Handle multi-modal content
            content_type = self.content.get("type", "text")
            if content_type == "text":
                return TFrameXMessage(role=self.role, content=self.content.get("text", ""))
            elif content_type == "image":
                # For now, return a placeholder
                mime_type = self.content.get("mimeType", "image/unknown")
                return TFrameXMessage(
                    role=self.role, 
                    content=f"[Image content: {mime_type}]"
                )
            else:
                return TFrameXMessage(
                    role=self.role,
                    content=f"[Unsupported content type: {content_type}]"
                )
        else:
            return TFrameXMessage(role=self.role, content=str(self.content))


@dataclass
class SamplingRequest:
    """A sampling request from an MCP server."""
    request_id: str
    server_alias: str
    messages: List[SamplingMessage]
    model_preferences: Optional[ModelPreferences] = None
    system_prompt: Optional[str] = None
    include_context: Optional[str] = None  # "none", "thisServer", "allServers"
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_mcp_params(cls, request_id: str, server_alias: str, 
                       params: Dict[str, Any]) -> "SamplingRequest":
        """Create from MCP sampling request parameters."""
        messages = [
            SamplingMessage.from_mcp(msg) 
            for msg in params.get("messages", [])
        ]
        
        model_prefs = None
        if "modelPreferences" in params:
            prefs = params["modelPreferences"]
            model_prefs = ModelPreferences(
                hints=prefs.get("hints", []),
                cost_priority=prefs.get("costPriority", 0.5),
                speed_priority=prefs.get("speedPriority", 0.5),
                intelligence_priority=prefs.get("intelligencePriority", 0.5)
            )
        
        return cls(
            request_id=request_id,
            server_alias=server_alias,
            messages=messages,
            model_preferences=model_prefs,
            system_prompt=params.get("systemPrompt"),
            include_context=params.get("includeContext", "none"),
            temperature=params.get("temperature"),
            max_tokens=params.get("maxTokens"),
            stop_sequences=params.get("stopSequences"),
            metadata=params.get("metadata", {})
        )


@dataclass
class SamplingResponse:
    """Response to a sampling request."""
    model: str  # Model that was used
    content: Union[str, Dict[str, Any]]  # Response content
    stop_reason: Optional[str] = None  # Why generation stopped
    
    def to_mcp_result(self) -> Dict[str, Any]:
        """Convert to MCP response format."""
        return {
            "model": self.model,
            "content": self.content,
            "stopReason": self.stop_reason
        }


class SamplingApprovalHandler:
    """Handles approval workflows for sampling requests."""
    
    def __init__(self, auto_approve: bool = False, 
                 approval_callback: Optional[Callable] = None):
        """
        Initialize the approval handler.
        
        Args:
            auto_approve: If True, automatically approve all requests (dev mode)
            approval_callback: Custom callback for approval UI
        """
        self._auto_approve = auto_approve
        self._approval_callback = approval_callback
        self._approval_history: List[Dict[str, Any]] = []
    
    async def request_approval(self, request: SamplingRequest) -> tuple[SamplingApprovalStatus, Optional[SamplingRequest]]:
        """
        Request approval for a sampling request.
        
        Returns:
            Tuple of (approval_status, modified_request)
        """
        # Log the request
        logger.info(f"Sampling approval requested from '{request.server_alias}' "
                   f"with {len(request.messages)} messages")
        
        # Record in history
        self._approval_history.append({
            "request_id": request.request_id,
            "server_alias": request.server_alias,
            "timestamp": asyncio.get_event_loop().time(),
            "message_count": len(request.messages)
        })
        
        if self._auto_approve:
            logger.warning("Auto-approving sampling request (dev mode)")
            return SamplingApprovalStatus.APPROVED, request
        
        if self._approval_callback:
            # Use custom approval UI
            try:
                status, modified = await self._approval_callback(request)
                return status, modified
            except Exception as e:
                logger.error(f"Approval callback error: {e}")
                return SamplingApprovalStatus.DENIED, None
        
        # Default: Log details and auto-approve with warning
        logger.warning("No approval UI configured, auto-approving with warning")
        self._log_request_details(request)
        return SamplingApprovalStatus.APPROVED, request
    
    def _log_request_details(self, request: SamplingRequest):
        """Log sampling request details for security audit."""
        logger.info(f"Sampling Request Details:")
        logger.info(f"  Server: {request.server_alias}")
        logger.info(f"  Request ID: {request.request_id}")
        logger.info(f"  Include Context: {request.include_context}")
        if request.model_preferences:
            logger.info(f"  Model Hints: {request.model_preferences.hints}")
        logger.info(f"  Messages:")
        for i, msg in enumerate(request.messages):
            content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
            logger.info(f"    [{i}] {msg.role}: {content_preview}")


class SamplingManager:
    """
    Manages MCP sampling requests with security and approval workflows.
    """
    
    def __init__(self, default_llm: Optional[BaseLLMWrapper] = None,
                 approval_handler: Optional[SamplingApprovalHandler] = None,
                 rate_limit_per_server: int = 10,
                 rate_limit_window: int = 60):
        """
        Initialize the sampling manager.
        
        Args:
            default_llm: Default LLM to use for sampling
            approval_handler: Handler for approval workflows
            rate_limit_per_server: Max requests per server per window
            rate_limit_window: Rate limit window in seconds
        """
        self._default_llm = default_llm
        self._approval_handler = approval_handler or SamplingApprovalHandler()
        self._rate_limit_per_server = rate_limit_per_server
        self._rate_limit_window = rate_limit_window
        
        # Rate limiting tracking
        self._request_counts: Dict[str, List[float]] = {}
        self._request_lock = asyncio.Lock()
        
        # Model selection cache
        self._model_cache: Dict[str, BaseLLMWrapper] = {}
    
    async def handle_sampling_request(self, request_id: str, server_alias: str,
                                    params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP sampling request.
        
        Args:
            request_id: Unique request ID
            server_alias: Alias of requesting server
            params: MCP sampling parameters
            
        Returns:
            MCP-formatted response or error
        """
        try:
            # Parse request
            request = SamplingRequest.from_mcp_params(request_id, server_alias, params)
            
            # Check rate limits
            if not await self._check_rate_limit(server_alias):
                logger.warning(f"Rate limit exceeded for server '{server_alias}'")
                return {
                    "error": {
                        "code": -32000,
                        "message": "Rate limit exceeded"
                    }
                }
            
            # Request approval
            status, approved_request = await self._approval_handler.request_approval(request)
            
            if status == SamplingApprovalStatus.DENIED:
                logger.info(f"Sampling request denied for '{server_alias}'")
                return {
                    "error": {
                        "code": -32001,
                        "message": "Sampling request denied by user"
                    }
                }
            
            # Use approved/modified request
            if status == SamplingApprovalStatus.MODIFIED:
                request = approved_request
            
            # Select appropriate LLM
            llm = await self._select_llm(request)
            if not llm:
                return {
                    "error": {
                        "code": -32002,
                        "message": "No suitable LLM available"
                    }
                }
            
            # Convert messages to TFrameX format
            tframex_messages = [msg.to_tframex_message() for msg in request.messages]
            
            # Add system prompt if provided
            if request.system_prompt:
                tframex_messages.insert(0, TFrameXMessage(
                    role="system",
                    content=request.system_prompt
                ))
            
            # Call LLM
            llm_params = {}
            if request.temperature is not None:
                llm_params["temperature"] = request.temperature
            if request.max_tokens is not None:
                llm_params["max_tokens"] = request.max_tokens
            if request.stop_sequences:
                llm_params["stop"] = request.stop_sequences
            
            response_msg = await llm.chat_completion(
                messages=tframex_messages,
                **llm_params
            )
            
            # Create response
            response = SamplingResponse(
                model=llm.model_id,
                content={
                    "type": "text",
                    "text": response_msg.content
                },
                stop_reason="stop"  # TODO: Get actual stop reason from LLM
            )
            
            return response.to_mcp_result()
            
        except Exception as e:
            logger.error(f"Sampling request error: {e}", exc_info=True)
            return {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _check_rate_limit(self, server_alias: str) -> bool:
        """Check if server is within rate limits."""
        async with self._request_lock:
            now = asyncio.get_event_loop().time()
            
            # Get request history for server
            if server_alias not in self._request_counts:
                self._request_counts[server_alias] = []
            
            # Remove old requests outside window
            cutoff = now - self._rate_limit_window
            self._request_counts[server_alias] = [
                t for t in self._request_counts[server_alias] if t > cutoff
            ]
            
            # Check limit
            if len(self._request_counts[server_alias]) >= self._rate_limit_per_server:
                return False
            
            # Add current request
            self._request_counts[server_alias].append(now)
            return True
    
    async def _select_llm(self, request: SamplingRequest) -> Optional[BaseLLMWrapper]:
        """
        Select appropriate LLM based on model preferences.
        
        For now, returns the default LLM. In production, this would
        implement sophisticated model selection based on preferences.
        """
        if not self._default_llm:
            logger.error("No default LLM configured for sampling")
            return None
        
        # TODO: Implement model selection based on preferences
        # - Match model hints
        # - Balance cost/speed/intelligence priorities
        # - Cache model instances
        
        return self._default_llm
    
    def get_capability(self) -> Dict[str, Any]:
        """Get the sampling capability declaration for MCP."""
        return {}  # Sampling capability has no configuration options
    
    async def cleanup(self):
        """Clean up resources."""
        # Clean up cached model instances
        for llm in self._model_cache.values():
            if hasattr(llm, "close"):
                try:
                    await llm.close()
                except Exception as e:
                    logger.error(f"Error closing cached LLM: {e}")
        
        self._model_cache.clear()
        self._request_counts.clear()


# Convenience function for creating a simple approval UI
async def console_approval_handler(request: SamplingRequest) -> tuple[SamplingApprovalStatus, Optional[SamplingRequest]]:
    """
    Simple console-based approval handler for development.
    
    In production, this would be replaced with a proper UI.
    """
    print("\n" + "="*60)
    print("SAMPLING APPROVAL REQUEST")
    print("="*60)
    print(f"Server: {request.server_alias}")
    print(f"Messages: {len(request.messages)}")
    
    for i, msg in enumerate(request.messages):
        print(f"\n[{i}] {msg.role.upper()}:")
        if isinstance(msg.content, str):
            print(f"  {msg.content}")
        else:
            print(f"  {json.dumps(msg.content, indent=2)}")
    
    if request.model_preferences:
        print(f"\nModel Preferences:")
        print(f"  Hints: {request.model_preferences.hints}")
        print(f"  Priorities: cost={request.model_preferences.cost_priority}, "
              f"speed={request.model_preferences.speed_priority}, "
              f"intelligence={request.model_preferences.intelligence_priority}")
    
    print("\n" + "-"*60)
    print("Options: [a]pprove, [d]eny, [m]odify")
    
    # In a real implementation, this would be async UI
    # For now, return auto-approval
    print("Auto-approving for development...")
    return SamplingApprovalStatus.APPROVED, request