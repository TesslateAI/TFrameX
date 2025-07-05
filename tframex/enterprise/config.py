"""
Enterprise Configuration

This module provides comprehensive configuration management for
TFrameX enterprise features.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class StorageConfig(BaseModel):
    """Configuration for storage backends."""
    type: str = Field(..., description="Storage backend type")
    enabled: bool = Field(default=True, description="Whether this storage is enabled")
    config: Dict[str, Any] = Field(default_factory=dict, description="Storage-specific configuration")


class MetricsConfig(BaseModel):
    """Configuration for metrics collection."""
    enabled: bool = Field(default=True, description="Whether metrics collection is enabled")
    backends: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Metrics backend configurations")
    default_labels: Dict[str, str] = Field(default_factory=dict, description="Default labels for all metrics")
    collection_interval: int = Field(default=60, description="Metric collection interval in seconds")
    buffer_size: int = Field(default=1000, description="Internal metrics buffer size")


class AuthenticationConfig(BaseModel):
    """Configuration for authentication providers."""
    enabled: bool = Field(default=True, description="Whether authentication is enabled")
    providers: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Authentication provider configurations")
    optional_paths: List[str] = Field(default_factory=list, description="Paths that don't require authentication")
    header_name: str = Field(default="Authorization", description="Authentication header name")
    cookie_name: str = Field(default="auth_token", description="Authentication cookie name")


class AuthorizationConfig(BaseModel):
    """Configuration for authorization and RBAC."""
    enabled: bool = Field(default=True, description="Whether authorization is enabled")
    default_role: str = Field(default="user", description="Default role for new users")
    enable_inheritance: bool = Field(default=True, description="Whether to enable role inheritance")
    enable_policies: bool = Field(default=True, description="Whether to enable policy evaluation")
    public_paths: List[str] = Field(default_factory=list, description="Paths that don't require authorization")
    cache_ttl: int = Field(default=300, description="Permission cache TTL in seconds")


class SessionConfig(BaseModel):
    """Configuration for session management."""
    enabled: bool = Field(default=True, description="Whether session management is enabled")
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")
    max_sessions_per_user: int = Field(default=5, description="Maximum sessions per user")
    cleanup_interval: int = Field(default=300, description="Session cleanup interval in seconds")
    session_id_length: int = Field(default=64, description="Length of session IDs")
    enable_rotation: bool = Field(default=True, description="Whether to enable session rotation")
    store_type: str = Field(default="database", description="Session store type (database, memory)")


class AuditConfig(BaseModel):
    """Configuration for audit logging."""
    enabled: bool = Field(default=True, description="Whether audit logging is enabled")
    buffer_size: int = Field(default=100, description="Audit event buffer size")
    flush_interval: int = Field(default=30, description="Audit flush interval in seconds")
    retention_days: int = Field(default=365, description="Audit log retention in days")
    compliance_mode: bool = Field(default=False, description="Enable additional compliance features")
    excluded_events: List[str] = Field(default_factory=list, description="Event types to exclude")
    excluded_users: List[str] = Field(default_factory=list, description="User IDs to exclude")
    log_requests: bool = Field(default=True, description="Whether to log all requests")
    log_responses: bool = Field(default=False, description="Whether to log responses")


class SecurityConfig(BaseModel):
    """Configuration for security features."""
    authentication: AuthenticationConfig = Field(default_factory=AuthenticationConfig)
    authorization: AuthorizationConfig = Field(default_factory=AuthorizationConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)


class EnterpriseConfig(BaseModel):
    """
    Comprehensive configuration for TFrameX enterprise features.
    """
    
    # Core settings
    enabled: bool = Field(default=True, description="Whether enterprise features are enabled")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Storage configuration
    storage: Dict[str, StorageConfig] = Field(default_factory=dict, description="Storage backend configurations")
    default_storage: str = Field(default="sqlite", description="Default storage backend to use")
    
    # Metrics configuration
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    
    # Security configuration
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # Integration settings
    integration: Dict[str, Any] = Field(default_factory=dict, description="Integration-specific settings")
    
    @validator('storage')
    def validate_storage_config(cls, v, values):
        """Validate storage configuration."""
        if not v:
            # Provide default storage configuration
            v = {
                "sqlite": StorageConfig(
                    type="sqlite",
                    config={"database_path": "tframex_enterprise.db"}
                )
            }
        else:
            # Convert dict configs to StorageConfig objects
            validated_storage = {}
            for name, config in v.items():
                if isinstance(config, dict):
                    validated_storage[name] = StorageConfig(**config)
                elif isinstance(config, StorageConfig):
                    validated_storage[name] = config
                else:
                    raise ValueError(f"Invalid storage config for '{name}': must be dict or StorageConfig")
            v = validated_storage
        return v
    
    @validator('default_storage')
    def validate_default_storage(cls, v, values):
        """Ensure default storage exists in storage configs."""
        storage_configs = values.get('storage', {})
        if v and v not in storage_configs:
            raise ValueError(f"Default storage '{v}' not found in storage configurations")
        return v
    
    def get_storage_config(self, name: Optional[str] = None) -> StorageConfig:
        """
        Get storage configuration by name.
        
        Args:
            name: Storage name, defaults to default_storage
            
        Returns:
            Storage configuration
        """
        storage_name = name or self.default_storage
        if storage_name not in self.storage:
            raise ValueError(f"Storage configuration '{storage_name}' not found")
        return self.storage[storage_name]
    
    def get_metrics_backend_config(self, backend_name: str) -> Dict[str, Any]:
        """
        Get metrics backend configuration.
        
        Args:
            backend_name: Backend name
            
        Returns:
            Backend configuration
        """
        return self.metrics.backends.get(backend_name, {})
    
    def get_auth_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """
        Get authentication provider configuration.
        
        Args:
            provider_name: Provider name
            
        Returns:
            Provider configuration
        """
        return self.security.authentication.providers.get(provider_name, {})
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


def load_enterprise_config(
    config_path: Optional[Union[str, Path]] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    env_prefix: str = "TFRAMEX_ENTERPRISE"
) -> EnterpriseConfig:
    """
    Load enterprise configuration from various sources.
    
    Priority order:
    1. Provided config_dict
    2. Configuration file (YAML or JSON)
    3. Environment variables
    4. Defaults
    
    Args:
        config_path: Path to configuration file
        config_dict: Configuration dictionary
        env_prefix: Environment variable prefix
        
    Returns:
        Loaded enterprise configuration
    """
    try:
        final_config = {}
        
        # 1. Load from file if provided
        if config_path:
            file_config = _load_config_file(config_path)
            if file_config:
                final_config.update(file_config)
                logger.info(f"Loaded enterprise config from file: {config_path}")
        
        # 2. Override with provided config dict
        if config_dict:
            final_config.update(config_dict)
            logger.info("Applied provided config dictionary")
        
        # 3. Override with environment variables
        env_config = _load_env_config(env_prefix)
        if env_config:
            final_config.update(env_config)
            logger.info(f"Applied environment variables with prefix: {env_prefix}")
        
        # 4. Create and validate configuration
        config = EnterpriseConfig(**final_config)
        
        logger.info(f"Enterprise configuration loaded successfully (environment: {config.environment})")
        return config
        
    except Exception as e:
        logger.error(f"Failed to load enterprise configuration: {e}")
        # Return default configuration
        logger.warning("Using default enterprise configuration")
        return EnterpriseConfig()


def _load_config_file(config_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Load configuration from file."""
    try:
        path = Path(config_path)
        
        if not path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                if not YAML_AVAILABLE:
                    raise ImportError("PyYAML not available for YAML configuration files")
                return yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {path.suffix}")
                
    except Exception as e:
        logger.error(f"Failed to load configuration file {config_path}: {e}")
        return None


def _load_env_config(prefix: str) -> Dict[str, Any]:
    """Load configuration from environment variables."""
    try:
        config = {}
        prefix = prefix.upper() + "_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert environment variable to config key
                config_key = key[len(prefix):].lower()
                
                # Handle nested configuration
                key_parts = config_key.split('_')
                current = config
                
                for part in key_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Convert value to appropriate type
                final_key = key_parts[-1]
                current[final_key] = _parse_env_value(value)
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to load environment configuration: {e}")
        return {}


def _parse_env_value(value: str) -> Any:
    """Parse environment variable value to appropriate type."""
    # Boolean values
    if value.lower() in ('true', 'yes', '1', 'on'):
        return True
    elif value.lower() in ('false', 'no', '0', 'off'):
        return False
    
    # Numeric values
    try:
        if '.' in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        pass
    
    # JSON values
    if value.startswith(('{', '[', '"')):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    
    # String value
    return value


def create_default_config(
    environment: str = "development",
    output_path: Optional[Union[str, Path]] = None
) -> EnterpriseConfig:
    """
    Create a default enterprise configuration.
    
    Args:
        environment: Target environment
        output_path: Optional path to save configuration
        
    Returns:
        Default enterprise configuration
    """
    try:
        # Create comprehensive default configuration
        config_dict = {
            "enabled": True,
            "environment": environment,
            "debug": environment == "development",
            
            "storage": {
                "sqlite": {
                    "type": "sqlite",
                    "enabled": True,
                    "config": {
                        "database_path": "data/tframex_enterprise.db",
                        "pool_size": 10,
                        "create_tables": True
                    }
                },
                "postgresql": {
                    "type": "postgresql",
                    "enabled": False,
                    "config": {
                        "host": "localhost",
                        "port": 5432,
                        "database": "tframex_enterprise",
                        "username": "tframex",
                        "password": "changeme",
                        "pool_size": 20,
                        "ssl_mode": "prefer"
                    }
                }
            },
            
            "default_storage": "sqlite",
            
            "metrics": {
                "enabled": True,
                "backends": {
                    "prometheus": {
                        "type": "prometheus",
                        "enabled": True,
                        "port": 8090,
                        "host": "0.0.0.0"
                    },
                    "custom": {
                        "type": "custom",
                        "enabled": True,
                        "backend_class": "tframex.enterprise.metrics.custom.LoggingMetricsBackend",
                        "backend_config": {
                            "log_level": "INFO"
                        }
                    }
                },
                "default_labels": {
                    "service": "tframex",
                    "environment": environment
                },
                "collection_interval": 60,
                "buffer_size": 1000
            },
            
            "security": {
                "authentication": {
                    "enabled": True,
                    "providers": {
                        "api_key": {
                            "type": "api_key",
                            "enabled": True,
                            "header_name": "X-API-Key",
                            "key_length": 32
                        },
                        "jwt": {
                            "type": "jwt",
                            "enabled": True,
                            "secret_key": "change-this-secret-key-in-production",
                            "algorithm": "HS256",
                            "expiration": 3600
                        }
                    },
                    "optional_paths": ["/health", "/metrics", "/docs"]
                },
                
                "authorization": {
                    "enabled": True,
                    "default_role": "user",
                    "enable_inheritance": True,
                    "enable_policies": True,
                    "public_paths": ["/health", "/metrics"],
                    "cache_ttl": 300
                },
                
                "session": {
                    "enabled": True,
                    "session_timeout": 3600,
                    "max_sessions_per_user": 5,
                    "cleanup_interval": 300,
                    "store_type": "database"
                },
                
                "audit": {
                    "enabled": True,
                    "buffer_size": 100,
                    "flush_interval": 30,
                    "retention_days": 365,
                    "compliance_mode": environment == "production",
                    "log_requests": True,
                    "log_responses": False
                }
            }
        }
        
        config = EnterpriseConfig(**config_dict)
        
        # Save to file if requested
        if output_path:
            _save_config_file(config, output_path)
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to create default configuration: {e}")
        raise


def _save_config_file(config: EnterpriseConfig, output_path: Union[str, Path]) -> None:
    """Save configuration to file."""
    try:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = config.dict(exclude_none=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                if not YAML_AVAILABLE:
                    raise ImportError("PyYAML not available for YAML output")
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            elif path.suffix.lower() == '.json':
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported output format: {path.suffix}")
        
        logger.info(f"Configuration saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to save configuration to {output_path}: {e}")
        raise


# Configuration validation utilities

def validate_config(config: EnterpriseConfig) -> List[str]:
    """
    Validate enterprise configuration and return list of issues.
    
    Args:
        config: Configuration to validate
        
    Returns:
        List of validation issues (empty if valid)
    """
    issues = []
    
    try:
        # Validate storage configuration
        if not config.storage:
            issues.append("No storage backends configured")
        elif config.default_storage not in config.storage:
            issues.append(f"Default storage '{config.default_storage}' not found in storage configurations")
        
        # Validate metrics configuration
        if config.metrics.enabled and not config.metrics.backends:
            issues.append("Metrics enabled but no backends configured")
        
        # Validate security configuration
        if config.security.authentication.enabled and not config.security.authentication.providers:
            issues.append("Authentication enabled but no providers configured")
        
        # Validate production settings
        if config.is_production():
            if config.debug:
                issues.append("Debug mode should be disabled in production")
            
            # Check for insecure JWT secrets
            jwt_config = config.get_auth_provider_config("jwt")
            if jwt_config.get("secret_key") == "change-this-secret-key-in-production":
                issues.append("JWT secret key should be changed in production")
        
        logger.info(f"Configuration validation completed with {len(issues)} issues")
        
    except Exception as e:
        issues.append(f"Configuration validation error: {str(e)}")
    
    return issues