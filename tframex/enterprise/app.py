"""
Enterprise TFrameX Application

This module extends the core TFrameX application with enterprise features
including metrics, storage, security, and audit logging.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Union

from ..app import TFrameXApp, TFrameXRuntimeContext
from ..models.primitives import MessageChunk
from ..util.llms import BaseLLMWrapper
from ..util.memory import BaseMemoryStore, InMemoryMemoryStore

from .config import EnterpriseConfig, load_enterprise_config
from .storage.factory import create_storage_backend
from .metrics.manager import MetricsManager
from .security.auth import AuthenticationProvider
from .security.rbac import RBACEngine
from .security.middleware import SecurityMiddleware, SecurityContext
from .security.session import SessionManager, DatabaseSessionStore, MemorySessionStore
from .security.audit import AuditLogger
from .models import User

logger = logging.getLogger("tframex.enterprise.app")


class EnterpriseApp(TFrameXApp):
    """
    Enterprise-enhanced TFrameX application with comprehensive
    business features including metrics, security, and audit logging.
    """
    
    def __init__(
        self,
        # TFrameX core parameters
        default_llm: Optional[BaseLLMWrapper] = None,
        default_memory_store_factory: Callable[[], BaseMemoryStore] = InMemoryMemoryStore,
        mcp_config_file: Optional[str] = "servers_config.json",
        enable_mcp_roots: bool = True,
        enable_mcp_sampling: bool = True,
        enable_mcp_experimental: bool = False,
        mcp_roots_allowed_paths: Optional[List[str]] = None,
        
        # Enterprise parameters
        enterprise_config: Optional[Union[str, Path, Dict[str, Any], EnterpriseConfig]] = None,
        auto_initialize: bool = True
    ):
        """
        Initialize Enterprise TFrameX application.
        
        Args:
            # Core TFrameX parameters (inherited)
            default_llm: Default LLM for agents
            default_memory_store_factory: Factory for memory stores
            mcp_config_file: MCP configuration file path
            enable_mcp_roots: Enable MCP roots capability
            enable_mcp_sampling: Enable MCP sampling capability
            enable_mcp_experimental: Enable experimental MCP features
            mcp_roots_allowed_paths: Allowed paths for MCP roots
            
            # Enterprise parameters
            enterprise_config: Enterprise configuration (file path, dict, or object)
            auto_initialize: Whether to automatically initialize enterprise features
        """
        # Initialize core TFrameX application
        super().__init__(
            default_llm=default_llm,
            default_memory_store_factory=default_memory_store_factory,
            mcp_config_file=mcp_config_file,
            enable_mcp_roots=enable_mcp_roots,
            enable_mcp_sampling=enable_mcp_sampling,
            enable_mcp_experimental=enable_mcp_experimental,
            mcp_roots_allowed_paths=mcp_roots_allowed_paths
        )
        
        # Load enterprise configuration
        self.enterprise_config = self._load_enterprise_config(enterprise_config)
        
        # Enterprise components
        self._storage_backends: Dict[str, Any] = {}
        self._metrics_manager: Optional[MetricsManager] = None
        self._rbac_engine: Optional[RBACEngine] = None
        self._session_manager: Optional[SessionManager] = None
        self._audit_logger: Optional[AuditLogger] = None
        self._security_middleware: Optional[SecurityMiddleware] = None
        self._auth_providers: Dict[str, AuthenticationProvider] = {}
        
        # Initialization state
        self._enterprise_initialized = False
        self._enterprise_running = False
        
        if auto_initialize and self.enterprise_config.enabled:
            # Initialize enterprise features in background
            asyncio.create_task(self._initialize_enterprise_async())
    
    def _load_enterprise_config(
        self, 
        config: Optional[Union[str, Path, Dict[str, Any], EnterpriseConfig]]
    ) -> EnterpriseConfig:
        """Load and validate enterprise configuration."""
        try:
            if isinstance(config, EnterpriseConfig):
                return config
            elif isinstance(config, dict):
                return EnterpriseConfig(**config)
            elif isinstance(config, (str, Path)):
                return load_enterprise_config(config_path=config)
            else:
                # Load default configuration
                return load_enterprise_config()
                
        except Exception as e:
            logger.error(f"Failed to load enterprise configuration: {e}")
            logger.warning("Using default enterprise configuration")
            return EnterpriseConfig()
    
    async def _initialize_enterprise_async(self) -> None:
        """Initialize enterprise features asynchronously."""
        try:
            await self.initialize_enterprise()
        except Exception as e:
            logger.error(f"Failed to initialize enterprise features: {e}")
    
    async def initialize_enterprise(self) -> None:
        """
        Initialize all enterprise features.
        
        This method sets up storage, metrics, security, and audit logging
        based on the enterprise configuration.
        """
        if self._enterprise_initialized:
            logger.debug("Enterprise features already initialized")
            return
        
        if not self.enterprise_config.enabled:
            logger.info("Enterprise features disabled in configuration")
            return
        
        try:
            logger.info("Initializing TFrameX Enterprise features...")
            
            # 1. Initialize storage backends
            await self._initialize_storage()
            
            # 2. Initialize metrics collection
            await self._initialize_metrics()
            
            # 3. Initialize security system
            await self._initialize_security()
            
            # 4. Initialize audit logging
            await self._initialize_audit()
            
            self._enterprise_initialized = True
            logger.info("TFrameX Enterprise initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enterprise features: {e}")
            raise
    
    async def _initialize_storage(self) -> None:
        """Initialize storage backends."""
        try:
            logger.info("Initializing storage backends...")
            
            for storage_name, storage_config in self.enterprise_config.storage.items():
                if not storage_config.enabled:
                    continue
                
                try:
                    storage_backend = await create_storage_backend(
                        storage_config.type,
                        storage_config.config
                    )
                    
                    self._storage_backends[storage_name] = storage_backend
                    logger.info(f"Initialized storage backend: {storage_name} ({storage_config.type})")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize storage backend {storage_name}: {e}")
                    if storage_name == self.enterprise_config.default_storage:
                        raise  # Fatal error for default storage
            
            if not self._storage_backends:
                raise RuntimeError("No storage backends were successfully initialized")
                
        except Exception as e:
            logger.error(f"Storage initialization failed: {e}")
            raise
    
    async def _initialize_metrics(self) -> None:
        """Initialize metrics collection system."""
        try:
            if not self.enterprise_config.metrics.enabled:
                logger.info("Metrics collection disabled")
                return
            
            logger.info("Initializing metrics collection...")
            
            # Create metrics manager
            metrics_config = {
                "enabled": True,
                "backends": self.enterprise_config.metrics.backends,
                "default_labels": self.enterprise_config.metrics.default_labels,
                "collection_interval": self.enterprise_config.metrics.collection_interval,
                "buffer_size": self.enterprise_config.metrics.buffer_size
            }
            
            self._metrics_manager = MetricsManager(metrics_config)
            await self._metrics_manager.start()
            
            logger.info("Metrics collection initialized successfully")
            
        except Exception as e:
            logger.error(f"Metrics initialization failed: {e}")
            # Non-fatal error
    
    async def _initialize_security(self) -> None:
        """Initialize security system."""
        try:
            logger.info("Initializing security system...")
            
            # Get default storage for security
            default_storage = self.get_storage()
            
            # Initialize authentication providers
            await self._initialize_auth_providers(default_storage)
            
            # Initialize RBAC engine
            await self._initialize_rbac(default_storage)
            
            # Initialize session manager
            await self._initialize_session_manager(default_storage)
            
            # Initialize audit logger
            if self.enterprise_config.security.audit.enabled:
                await self._initialize_audit_logger(default_storage)
            
            # Initialize security middleware
            await self._initialize_security_middleware()
            
            logger.info("Security system initialized successfully")
            
        except Exception as e:
            logger.error(f"Security initialization failed: {e}")
            raise
    
    async def _initialize_auth_providers(self, storage) -> None:
        """Initialize authentication providers."""
        try:
            from .security.auth import APIKeyProvider, BasicAuthProvider, JWTProvider, OAuth2Provider
            
            auth_config = self.enterprise_config.security.authentication
            if not auth_config.enabled:
                return
            
            provider_classes = {
                "api_key": APIKeyProvider,
                "basic": BasicAuthProvider,
                "jwt": JWTProvider,
                "oauth2": OAuth2Provider
            }
            
            for provider_name, provider_config in auth_config.providers.items():
                if not provider_config.get("enabled", True):
                    continue
                
                provider_type = provider_config.get("type", provider_name)
                provider_class = provider_classes.get(provider_type)
                
                if not provider_class:
                    logger.warning(f"Unknown authentication provider type: {provider_type}")
                    continue
                
                try:
                    # Add storage to provider config
                    full_config = {**provider_config, "storage": storage}
                    provider = provider_class(full_config)
                    await provider.initialize()
                    
                    self._auth_providers[provider_name] = provider
                    logger.info(f"Initialized authentication provider: {provider_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize auth provider {provider_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Authentication providers initialization failed: {e}")
            raise
    
    async def _initialize_rbac(self, storage) -> None:
        """Initialize RBAC engine."""
        try:
            rbac_config = {
                "storage": storage,
                **self.enterprise_config.security.authorization.dict()
            }
            
            self._rbac_engine = RBACEngine(rbac_config)
            await self._rbac_engine.initialize()
            
            logger.info("RBAC engine initialized successfully")
            
        except Exception as e:
            logger.error(f"RBAC initialization failed: {e}")
            raise
    
    async def _initialize_session_manager(self, storage) -> None:
        """Initialize session manager."""
        try:
            session_config = self.enterprise_config.security.session
            if not session_config.enabled:
                return
            
            # Create session store
            if session_config.store_type == "database":
                session_store = DatabaseSessionStore(storage)
            else:
                session_store = MemorySessionStore()
            
            manager_config = {
                "session_store": session_store,
                **session_config.dict(exclude={"store_type"})
            }
            
            self._session_manager = SessionManager(manager_config)
            await self._session_manager.start()
            
            logger.info("Session manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Session manager initialization failed: {e}")
            raise
    
    async def _initialize_audit_logger(self, storage) -> None:
        """Initialize audit logger."""
        try:
            audit_config = {
                "storage": storage,
                **self.enterprise_config.security.audit.dict()
            }
            
            self._audit_logger = AuditLogger(audit_config)
            await self._audit_logger.start()
            
            logger.info("Audit logger initialized successfully")
            
        except Exception as e:
            logger.error(f"Audit logger initialization failed: {e}")
            raise
    
    async def _initialize_security_middleware(self) -> None:
        """Initialize security middleware stack."""
        try:
            from .security.middleware import (
                AuthenticationMiddleware, AuthorizationMiddleware, 
                AuditMiddleware, SecurityMiddleware
            )
            
            # Create authentication middleware
            auth_config = self.enterprise_config.security.authentication.dict()
            # Remove providers from config to avoid overriding our provider objects
            auth_config.pop("providers", None)
            auth_middleware = AuthenticationMiddleware({
                "providers": list(self._auth_providers.values()),
                **auth_config
            })
            
            # Create authorization middleware
            authz_middleware = AuthorizationMiddleware({
                "rbac_engine": self._rbac_engine,
                **self.enterprise_config.security.authorization.dict()
            })
            
            # Create audit middleware
            audit_middleware = None
            if self._audit_logger:
                audit_middleware = AuditMiddleware({
                    "audit_logger": self._audit_logger,
                    **self.enterprise_config.security.audit.dict()
                })
            
            # Create security middleware stack
            self._security_middleware = SecurityMiddleware({
                "auth_middleware": auth_middleware,
                "authz_middleware": authz_middleware,
                "audit_middleware": audit_middleware,
                "session_manager": self._session_manager
            })
            
            logger.info("Security middleware initialized successfully")
            
        except Exception as e:
            logger.error(f"Security middleware initialization failed: {e}")
            raise
    
    async def _initialize_audit(self) -> None:
        """Initialize audit logging (already done in security)."""
        # Audit logging is initialized as part of security system
        pass
    
    async def start_enterprise(self) -> None:
        """
        Start all enterprise services.
        
        This method should be called to start background services
        like metrics collection and session cleanup.
        """
        if self._enterprise_running:
            logger.debug("Enterprise services already running")
            return
        
        if not self._enterprise_initialized:
            await self.initialize_enterprise()
        
        try:
            logger.info("Starting enterprise services...")
            
            # Start services that need background tasks
            if self._metrics_manager:
                await self._metrics_manager.start()
            
            if self._session_manager:
                await self._session_manager.start()
            
            if self._audit_logger:
                await self._audit_logger.start()
            
            self._enterprise_running = True
            logger.info("Enterprise services started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start enterprise services: {e}")
            raise
    
    async def stop_enterprise(self) -> None:
        """
        Stop all enterprise services gracefully.
        """
        if not self._enterprise_running:
            logger.debug("Enterprise services not running")
            return
        
        try:
            logger.info("Stopping enterprise services...")
            
            # Stop services in reverse order
            if self._audit_logger:
                await self._audit_logger.stop()
            
            if self._session_manager:
                await self._session_manager.stop()
            
            if self._metrics_manager:
                await self._metrics_manager.stop()
            
            # Close storage backends
            for storage_name, storage in self._storage_backends.items():
                try:
                    if hasattr(storage, 'close'):
                        await storage.close()
                    logger.debug(f"Closed storage backend: {storage_name}")
                except Exception as e:
                    logger.error(f"Error closing storage {storage_name}: {e}")
            
            self._enterprise_running = False
            logger.info("Enterprise services stopped successfully")
            
        except Exception as e:
            logger.error(f"Failed to stop enterprise services: {e}")
    
    def get_storage(self, name: Optional[str] = None) -> Any:
        """
        Get storage backend by name.
        
        Args:
            name: Storage backend name (defaults to default_storage)
            
        Returns:
            Storage backend instance
        """
        storage_name = name or self.enterprise_config.default_storage
        
        if storage_name not in self._storage_backends:
            raise ValueError(f"Storage backend '{storage_name}' not available")
        
        return self._storage_backends[storage_name]
    
    def get_metrics_manager(self) -> Optional[MetricsManager]:
        """Get metrics manager instance."""
        return self._metrics_manager
    
    def get_rbac_engine(self) -> Optional[RBACEngine]:
        """Get RBAC engine instance."""
        return self._rbac_engine
    
    def get_session_manager(self) -> Optional[SessionManager]:
        """Get session manager instance."""
        return self._session_manager
    
    def get_audit_logger(self) -> Optional[AuditLogger]:
        """Get audit logger instance."""
        return self._audit_logger
    
    def get_security_middleware(self) -> Optional[SecurityMiddleware]:
        """Get security middleware instance."""
        return self._security_middleware
    
    def run_context(
        self,
        llm_override: Optional[BaseLLMWrapper] = None,
        user: Optional[User] = None,
        security_context: Optional[SecurityContext] = None
    ) -> "EnterpriseRuntimeContext":
        """
        Create enterprise runtime context with security support.
        
        Args:
            llm_override: LLM override for this context
            user: Authenticated user for this context
            security_context: Security context for this session
            
        Returns:
            Enterprise runtime context
        """
        ctx_llm = llm_override or self.default_llm
        return EnterpriseRuntimeContext(
            self, 
            llm=ctx_llm, 
            mcp_manager=self._mcp_manager,
            user=user,
            security_context=security_context
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check on enterprise features.
        
        Returns:
            Health status information
        """
        health = {
            "healthy": True,
            "enterprise_enabled": self.enterprise_config.enabled,
            "enterprise_initialized": self._enterprise_initialized,
            "enterprise_running": self._enterprise_running,
            "components": {}
        }
        
        try:
            # Check storage backends
            storage_health = {}
            for name, storage in self._storage_backends.items():
                try:
                    if hasattr(storage, 'health_check'):
                        storage_health[name] = await storage.health_check()
                    else:
                        storage_health[name] = {"healthy": True, "type": storage.__class__.__name__}
                except Exception as e:
                    storage_health[name] = {"healthy": False, "error": str(e)}
                    health["healthy"] = False
            
            health["components"]["storage"] = storage_health
            
            # Check metrics manager
            if self._metrics_manager:
                try:
                    health["components"]["metrics"] = await self._metrics_manager.health_check()
                except Exception as e:
                    health["components"]["metrics"] = {"healthy": False, "error": str(e)}
                    health["healthy"] = False
            
            # Check RBAC engine
            if self._rbac_engine:
                try:
                    health["components"]["rbac"] = await self._rbac_engine.health_check()
                except Exception as e:
                    health["components"]["rbac"] = {"healthy": False, "error": str(e)}
                    health["healthy"] = False
            
            # Check session manager
            if self._session_manager:
                try:
                    health["components"]["session"] = await self._session_manager.health_check()
                except Exception as e:
                    health["components"]["session"] = {"healthy": False, "error": str(e)}
                    health["healthy"] = False
            
            # Check audit logger
            if self._audit_logger:
                try:
                    health["components"]["audit"] = await self._audit_logger.health_check()
                except Exception as e:
                    health["components"]["audit"] = {"healthy": False, "error": str(e)}
                    health["healthy"] = False
            
        except Exception as e:
            health["healthy"] = False
            health["error"] = str(e)
        
        return health
    
    # Context manager support
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_enterprise()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_enterprise()


class EnterpriseRuntimeContext(TFrameXRuntimeContext):
    """
    Enterprise-enhanced runtime context with security and audit support.
    """
    
    def __init__(
        self,
        app: EnterpriseApp,
        llm: Optional[BaseLLMWrapper],
        mcp_manager=None,
        user: Optional[User] = None,
        security_context: Optional[SecurityContext] = None
    ):
        """
        Initialize enterprise runtime context.
        
        Args:
            app: Enterprise application instance
            llm: LLM for this context
            mcp_manager: MCP manager instance
            user: Authenticated user
            security_context: Security context
        """
        super().__init__(app, llm, mcp_manager)
        
        self.enterprise_app = app
        self.user = user
        self.security_context = security_context or SecurityContext()
        
        # Update security context with user info
        if user:
            self.security_context.user = user
            self.security_context.authenticated = True
    
    async def call_agent(
        self, 
        agent_name: str, 
        input_message: Union[str, Any], 
        **kwargs: Any
    ) -> Any:
        """
        Call agent with enterprise security and audit integration.
        
        Args:
            agent_name: Agent name to call
            input_message: Input message
            **kwargs: Additional arguments
            
        Returns:
            Agent response
        """
        try:
            # Security check if RBAC is enabled
            if self.enterprise_app.get_rbac_engine():
                if self.user:
                    await self.enterprise_app.get_rbac_engine().check_permission(
                        self.user, "agents", "execute"
                    )
                else:
                    logger.warning("Agent call without authenticated user")
            
            # Audit log the agent call
            if self.enterprise_app.get_audit_logger():
                await self.enterprise_app.get_audit_logger().log_event(
                    event_type="user_action",
                    user_id=self.user.id if self.user else None,
                    resource="agent",
                    action="call",
                    details={
                        "agent_name": agent_name,
                        "input_length": len(str(input_message))
                    }
                )
            
            # Metrics collection
            if self.enterprise_app.get_metrics_manager():
                await self.enterprise_app.get_metrics_manager().increment_counter(
                    "tframex.agents.calls.total",
                    labels={"agent_name": agent_name}
                )
            
            # Call parent implementation
            result = await super().call_agent(agent_name, input_message, **kwargs)
            
            # Log successful execution
            if self.enterprise_app.get_audit_logger():
                await self.enterprise_app.get_audit_logger().log_event(
                    event_type="user_action",
                    user_id=self.user.id if self.user else None,
                    resource="agent",
                    action="call",
                    outcome="success",
                    details={
                        "agent_name": agent_name,
                        "response_length": len(str(result))
                    }
                )
            
            return result
            
        except Exception as e:
            # Log failed execution
            if self.enterprise_app.get_audit_logger():
                await self.enterprise_app.get_audit_logger().log_event(
                    event_type="user_action",
                    user_id=self.user.id if self.user else None,
                    resource="agent",
                    action="call",
                    outcome="failure",
                    details={
                        "agent_name": agent_name,
                        "error": str(e)
                    }
                )
            
            # Metrics for failures
            if self.enterprise_app.get_metrics_manager():
                await self.enterprise_app.get_metrics_manager().increment_counter(
                    "tframex.agents.errors.total",
                    labels={"agent_name": agent_name, "error_type": e.__class__.__name__}
                )
            
            raise
    
    async def call_agent_stream(
        self, 
        agent_name: str, 
        input_message: Union[str, Any], 
        **kwargs: Any
    ) -> AsyncGenerator[MessageChunk, None]:
        """
        Call agent with streaming response and enterprise security/audit integration.
        
        Args:
            agent_name: Agent name to call
            input_message: Input message
            **kwargs: Additional arguments
            
        Yields:
            MessageChunk: Individual chunks of the streaming response
        """
        try:
            # Security check if RBAC is enabled
            if self.enterprise_app.get_rbac_engine():
                if self.user:
                    await self.enterprise_app.get_rbac_engine().check_permission(
                        self.user, "agents", "execute"
                    )
                else:
                    logger.warning("Agent call without authenticated user")
            
            # Audit log the agent call start
            if self.enterprise_app.get_audit_logger():
                await self.enterprise_app.get_audit_logger().log_event(
                    event_type="user_action",
                    user_id=self.user.id if self.user else None,
                    resource="agent",
                    action="call_stream",
                    details={
                        "agent_name": agent_name,
                        "input_length": len(str(input_message))
                    }
                )
            
            # Metrics collection
            if self.enterprise_app.get_metrics_manager():
                await self.enterprise_app.get_metrics_manager().increment_counter(
                    "tframex.agents.stream_calls.total",
                    labels={"agent_name": agent_name}
                )
            
            # Call parent implementation for streaming
            stream_generator = super().call_agent_stream(agent_name, input_message, **kwargs)
            
            # Track streaming metrics
            chunk_count = 0
            total_content_length = 0
            
            async for chunk in stream_generator:
                chunk_count += 1
                if chunk.content:
                    total_content_length += len(chunk.content)
                yield chunk
            
            # Log successful streaming execution
            if self.enterprise_app.get_audit_logger():
                await self.enterprise_app.get_audit_logger().log_event(
                    event_type="user_action",
                    user_id=self.user.id if self.user else None,
                    resource="agent",
                    action="call_stream",
                    outcome="success",
                    details={
                        "agent_name": agent_name,
                        "chunk_count": chunk_count,
                        "total_content_length": total_content_length
                    }
                )
            
            # Final metrics for successful streaming
            if self.enterprise_app.get_metrics_manager():
                await self.enterprise_app.get_metrics_manager().increment_counter(
                    "tframex.agents.stream_chunks.total",
                    labels={"agent_name": agent_name},
                    value=chunk_count
                )
                
        except Exception as e:
            # Log failed streaming execution
            if self.enterprise_app.get_audit_logger():
                await self.enterprise_app.get_audit_logger().log_event(
                    event_type="user_action",
                    user_id=self.user.id if self.user else None,
                    resource="agent",
                    action="call_stream",
                    outcome="failure",
                    details={
                        "agent_name": agent_name,
                        "error": str(e)
                    }
                )
            
            # Metrics for streaming failures
            if self.enterprise_app.get_metrics_manager():
                await self.enterprise_app.get_metrics_manager().increment_counter(
                    "tframex.agents.stream_errors.total",
                    labels={"agent_name": agent_name, "error_type": e.__class__.__name__}
                )
            
            raise
    
    def get_storage(self, name: Optional[str] = None):
        """Get storage backend."""
        return self.enterprise_app.get_storage(name)
    
    def get_metrics_manager(self):
        """Get metrics manager."""
        return self.enterprise_app.get_metrics_manager()
    
    def get_rbac_engine(self):
        """Get RBAC engine."""
        return self.enterprise_app.get_rbac_engine()
    
    def get_audit_logger(self):
        """Get audit logger."""
        return self.enterprise_app.get_audit_logger()