# tframex/mcp/capabilities.py
"""
MCP capability negotiation and feature detection for TFrameX.
Implements comprehensive capability exchange for backward compatibility.
"""
import logging
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("tframex.mcp.capabilities")


class CapabilityStatus(Enum):
    """Status of a capability."""
    SUPPORTED = "supported"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
    UNSUPPORTED = "unsupported"


@dataclass
class ServerCapability:
    """Represents a server capability."""
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None
    experimental: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP format."""
        result = {}
        if self.tools is not None:
            result["tools"] = self.tools
        if self.resources is not None:
            result["resources"] = self.resources
        if self.prompts is not None:
            result["prompts"] = self.prompts
        if self.logging is not None:
            result["logging"] = self.logging
        if self.experimental:
            result["experimental"] = self.experimental
        return result


@dataclass
class ClientCapability:
    """Represents client capabilities."""
    roots: Optional[Dict[str, Any]] = None
    sampling: Optional[Dict[str, Any]] = None
    experimental: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP format."""
        result = {}
        if self.roots is not None:
            result["roots"] = self.roots
        if self.sampling is not None:
            result["sampling"] = self.sampling
        if self.experimental:
            result["experimental"] = self.experimental
        return result


@dataclass
class ProtocolCapability:
    """Combined protocol capabilities."""
    protocol_version: str = "2025-06-18"
    client_capabilities: Optional[ClientCapability] = None
    server_capabilities: Optional[ServerCapability] = None
    
    def get_supported_features(self) -> Set[str]:
        """Get set of all supported features."""
        features = set()
        
        # Client features
        if self.client_capabilities:
            if self.client_capabilities.roots:
                features.add("client.roots")
            if self.client_capabilities.sampling:
                features.add("client.sampling")
        
        # Server features
        if self.server_capabilities:
            if self.server_capabilities.tools:
                features.add("server.tools")
            if self.server_capabilities.resources:
                features.add("server.resources")
            if self.server_capabilities.prompts:
                features.add("server.prompts")
            if self.server_capabilities.logging:
                features.add("server.logging")
        
        return features


class CapabilityManager:
    """
    Manages capability negotiation and feature detection for TFrameX.
    """
    
    def __init__(self, 
                 enable_roots: bool = True,
                 enable_sampling: bool = True,
                 enable_experimental: bool = False):
        """
        Initialize capability manager.
        
        Args:
            enable_roots: Enable roots capability
            enable_sampling: Enable sampling capability
            enable_experimental: Enable experimental features
        """
        self._enable_roots = enable_roots
        self._enable_sampling = enable_sampling
        self._enable_experimental = enable_experimental
        
        # Track negotiated capabilities per server
        self._server_capabilities: Dict[str, ServerCapability] = {}
        
        # Feature compatibility matrix
        self._compatibility_matrix = {
            "2025-06-18": {
                "client.roots": CapabilityStatus.SUPPORTED,
                "client.sampling": CapabilityStatus.SUPPORTED,
                "server.tools": CapabilityStatus.SUPPORTED,
                "server.resources": CapabilityStatus.SUPPORTED,
                "server.prompts": CapabilityStatus.SUPPORTED,
                "server.logging": CapabilityStatus.SUPPORTED,
            },
            "2024-12-01": {  # Older version example
                "client.roots": CapabilityStatus.UNSUPPORTED,
                "client.sampling": CapabilityStatus.EXPERIMENTAL,
                "server.tools": CapabilityStatus.SUPPORTED,
                "server.resources": CapabilityStatus.SUPPORTED,
                "server.prompts": CapabilityStatus.DEPRECATED,
                "server.logging": CapabilityStatus.UNSUPPORTED,
            }
        }
    
    def build_client_capabilities(self, 
                                roots_manager: Optional[Any] = None,
                                sampling_manager: Optional[Any] = None) -> ClientCapability:
        """
        Build client capabilities based on configuration.
        
        Args:
            roots_manager: RootsManager instance if available
            sampling_manager: SamplingManager instance if available
            
        Returns:
            ClientCapability object
        """
        capabilities = ClientCapability()
        
        # Roots capability
        if self._enable_roots and roots_manager:
            capabilities.roots = roots_manager.get_capability()
            logger.info("Roots capability enabled")
        
        # Sampling capability
        if self._enable_sampling and sampling_manager:
            capabilities.sampling = sampling_manager.get_capability()
            logger.info("Sampling capability enabled")
        
        # Experimental features
        if self._enable_experimental:
            capabilities.experimental = {
                "progressReporting": {},
                "multiModalContent": {
                    "supportedTypes": ["text", "image"]
                },
                "structuredOutput": {
                    "schemaValidation": True
                }
            }
            logger.info("Experimental capabilities enabled")
        
        return capabilities
    
    def negotiate_capabilities(self, 
                             client_cap: ClientCapability,
                             server_cap: ServerCapability,
                             protocol_version: str = "2025-06-18") -> ProtocolCapability:
        """
        Negotiate capabilities between client and server.
        
        Args:
            client_cap: Client capabilities
            server_cap: Server capabilities
            protocol_version: Protocol version
            
        Returns:
            Negotiated protocol capabilities
        """
        # Check version compatibility
        if protocol_version not in self._compatibility_matrix:
            logger.warning(f"Unknown protocol version: {protocol_version}")
            protocol_version = "2025-06-18"  # Fallback to latest
        
        compatibility = self._compatibility_matrix[protocol_version]
        
        # Filter client capabilities based on compatibility
        negotiated_client = ClientCapability()
        
        if client_cap.roots and self._check_feature_status("client.roots", compatibility):
            negotiated_client.roots = client_cap.roots
        
        if client_cap.sampling and self._check_feature_status("client.sampling", compatibility):
            negotiated_client.sampling = client_cap.sampling
        
        # Filter experimental features
        if client_cap.experimental and self._enable_experimental:
            negotiated_client.experimental = self._filter_experimental_features(
                client_cap.experimental, 
                server_cap.experimental if server_cap else {}
            )
        
        # Server capabilities are accepted as-is (client adapts to server)
        negotiated = ProtocolCapability(
            protocol_version=protocol_version,
            client_capabilities=negotiated_client,
            server_capabilities=server_cap
        )
        
        # Log negotiation result
        supported_features = negotiated.get_supported_features()
        logger.info(f"Capability negotiation complete. Features: {supported_features}")
        
        return negotiated
    
    def _check_feature_status(self, feature: str, compatibility: Dict[str, CapabilityStatus]) -> bool:
        """Check if a feature should be enabled based on compatibility."""
        status = compatibility.get(feature, CapabilityStatus.UNSUPPORTED)
        
        if status == CapabilityStatus.SUPPORTED:
            return True
        elif status == CapabilityStatus.EXPERIMENTAL:
            return self._enable_experimental
        elif status == CapabilityStatus.DEPRECATED:
            logger.warning(f"Feature '{feature}' is deprecated in this protocol version")
            return True  # Still enable but warn
        else:
            return False
    
    def _filter_experimental_features(self, 
                                    client_exp: Dict[str, Any],
                                    server_exp: Dict[str, Any]) -> Dict[str, Any]:
        """Filter experimental features based on mutual support."""
        filtered = {}
        
        for feature, config in client_exp.items():
            if feature in server_exp:
                # Both support the experimental feature
                filtered[feature] = config
                logger.debug(f"Experimental feature '{feature}' mutually supported")
        
        return filtered
    
    def store_server_capabilities(self, server_alias: str, capabilities: ServerCapability) -> None:
        """Store negotiated server capabilities."""
        self._server_capabilities[server_alias] = capabilities
        logger.debug(f"Stored capabilities for server '{server_alias}'")
    
    def get_server_capabilities(self, server_alias: str) -> Optional[ServerCapability]:
        """Get stored server capabilities."""
        return self._server_capabilities.get(server_alias)
    
    def is_feature_supported(self, server_alias: str, feature: str) -> bool:
        """
        Check if a specific feature is supported by a server.
        
        Args:
            server_alias: Server to check
            feature: Feature name (e.g., "tools", "resources")
            
        Returns:
            True if feature is supported
        """
        capabilities = self._server_capabilities.get(server_alias)
        if not capabilities:
            return False
        
        # Map feature names to capability attributes
        feature_map = {
            "tools": capabilities.tools is not None,
            "resources": capabilities.resources is not None,
            "prompts": capabilities.prompts is not None,
            "logging": capabilities.logging is not None,
        }
        
        return feature_map.get(feature, False)
    
    def get_compatibility_report(self) -> Dict[str, Any]:
        """Generate a compatibility report."""
        report = {
            "client_features": {
                "roots": "enabled" if self._enable_roots else "disabled",
                "sampling": "enabled" if self._enable_sampling else "disabled",
                "experimental": "enabled" if self._enable_experimental else "disabled"
            },
            "server_compatibility": {}
        }
        
        for server_alias, capabilities in self._server_capabilities.items():
            features = []
            if capabilities.tools:
                features.append("tools")
            if capabilities.resources:
                features.append("resources")
            if capabilities.prompts:
                features.append("prompts")
            if capabilities.logging:
                features.append("logging")
            
            report["server_compatibility"][server_alias] = {
                "supported_features": features,
                "experimental_features": list(capabilities.experimental.keys()) if capabilities.experimental else []
            }
        
        return report


class BackwardCompatibilityAdapter:
    """
    Provides backward compatibility for older MCP protocol versions.
    """
    
    def __init__(self, protocol_version: str):
        """
        Initialize adapter for specific protocol version.
        
        Args:
            protocol_version: Target protocol version
        """
        self.protocol_version = protocol_version
        self._adapters = {
            "2024-12-01": self._adapt_2024_12_01,
            # Add more version adapters as needed
        }
    
    def adapt_request(self, method: str, params: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        Adapt a request for backward compatibility.
        
        Args:
            method: Request method
            params: Request parameters
            
        Returns:
            Adapted (method, params)
        """
        adapter = self._adapters.get(self.protocol_version)
        if adapter:
            return adapter(method, params, is_request=True)
        return method, params
    
    def adapt_response(self, method: str, result: Any) -> Any:
        """
        Adapt a response for backward compatibility.
        
        Args:
            method: Request method that generated this response
            result: Response result
            
        Returns:
            Adapted result
        """
        adapter = self._adapters.get(self.protocol_version)
        if adapter:
            _, adapted = adapter(method, result, is_request=False)
            return adapted
        return result
    
    def _adapt_2024_12_01(self, method: str, data: Any, is_request: bool) -> tuple[str, Any]:
        """Adapter for 2024-12-01 protocol version."""
        # Example adaptations for older protocol
        
        if is_request:
            # Adapt requests to older format
            if method == "tools/list":
                # Older version might not support pagination
                if isinstance(data, dict) and "cursor" in data:
                    data = {}  # Remove pagination
            
            elif method == "prompts/list":
                # Prompts might be called something else in older version
                method = "templates/list"
        
        else:
            # Adapt responses from older format
            if method == "initialize":
                # Ensure capabilities have expected structure
                if isinstance(data, dict) and "capabilities" in data:
                    caps = data["capabilities"]
                    # Older version might not have all capability fields
                    if "logging" not in caps:
                        caps["logging"] = None
        
        return method, data