"""
Storage Backend Factory

This module provides factory functions for creating storage backends
based on configuration.
"""

import logging
from typing import Any, Dict

from .base import BaseStorage
from .memory import InMemoryStorage
from .sqlite import SQLiteStorage

logger = logging.getLogger(__name__)

# Optional backends that require additional dependencies
try:
    from .postgresql import PostgreSQLStorage
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    from .s3 import S3Storage
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

try:
    from .redis import RedisStorage
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


async def create_storage_backend(storage_type: str, config: Dict[str, Any]) -> BaseStorage:
    """
    Create a storage backend instance based on type and configuration.
    
    Args:
        storage_type: Type of storage backend to create
        config: Configuration for the storage backend
        
    Returns:
        Initialized storage backend instance
        
    Raises:
        ValueError: If storage type is not supported
        ImportError: If required dependencies are not available
    """
    try:
        storage_type = storage_type.lower()
        
        # Memory storage
        if storage_type == "memory":
            storage = InMemoryStorage(config)
            await storage.initialize()
            return storage
        
        # SQLite storage
        elif storage_type == "sqlite":
            storage = SQLiteStorage(config)
            await storage.initialize()
            return storage
        
        # PostgreSQL storage
        elif storage_type == "postgresql":
            if not POSTGRESQL_AVAILABLE:
                raise ImportError(
                    "PostgreSQL storage requires additional dependencies. "
                    "Install with: pip install asyncpg"
                )
            storage = PostgreSQLStorage(config)
            await storage.initialize()
            return storage
        
        # S3 storage
        elif storage_type == "s3":
            if not S3_AVAILABLE:
                raise ImportError(
                    "S3 storage requires additional dependencies. "
                    "Install with: pip install aioboto3"
                )
            storage = S3Storage(config)
            await storage.initialize()
            return storage
        
        # Redis storage
        elif storage_type == "redis":
            if not REDIS_AVAILABLE:
                raise ImportError(
                    "Redis storage requires additional dependencies. "
                    "Install with: pip install redis[hiredis]"
                )
            storage = RedisStorage(config)
            await storage.initialize()
            return storage
        
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
            
    except Exception as e:
        logger.error(f"Failed to create storage backend '{storage_type}': {e}")
        raise


def get_available_storage_types() -> Dict[str, bool]:
    """
    Get list of available storage types and their availability.
    
    Returns:
        Dictionary mapping storage type to availability
    """
    return {
        "memory": True,
        "sqlite": True,
        "postgresql": POSTGRESQL_AVAILABLE,
        "s3": S3_AVAILABLE,
        "redis": REDIS_AVAILABLE
    }


def validate_storage_config(storage_type: str, config: Dict[str, Any]) -> bool:
    """
    Validate storage configuration for a given type.
    
    Args:
        storage_type: Storage type to validate
        config: Configuration to validate
        
    Returns:
        True if configuration is valid
        
    Raises:
        ValueError: If configuration is invalid
    """
    storage_type = storage_type.lower()
    
    if storage_type == "memory":
        # Memory storage has minimal configuration requirements
        return True
    
    elif storage_type == "sqlite":
        required_fields = ["database_path"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"SQLite storage missing required field: {field}")
        return True
    
    elif storage_type == "postgresql":
        required_fields = ["host", "database", "username", "password"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"PostgreSQL storage missing required field: {field}")
        return True
    
    elif storage_type == "s3":
        required_fields = ["bucket_name"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"S3 storage missing required field: {field}")
        return True
    
    elif storage_type == "redis":
        # Redis has sensible defaults for all fields
        return True
    
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")


def get_storage_config_template(storage_type: str) -> Dict[str, Any]:
    """
    Get a configuration template for a storage type.
    
    Args:
        storage_type: Storage type
        
    Returns:
        Configuration template
    """
    storage_type = storage_type.lower()
    
    if storage_type == "memory":
        return {
            "max_size": 10000,
            "cleanup_interval": 300
        }
    
    elif storage_type == "sqlite":
        return {
            "database_path": "data/tframex_enterprise.db",
            "pool_size": 10,
            "create_tables": True,
            "wal_mode": True,
            "foreign_keys": True
        }
    
    elif storage_type == "postgresql":
        return {
            "host": "localhost",
            "port": 5432,
            "database": "tframex_enterprise",
            "username": "tframex",
            "password": "changeme",
            "pool_size": 20,
            "pool_max_size": 50,
            "ssl_mode": "prefer",
            "command_timeout": 60,
            "create_tables": True
        }
    
    elif storage_type == "s3":
        return {
            "bucket_name": "tframex-enterprise-data",
            "region": "us-east-1",
            "aws_access_key_id": None,  # Use IAM roles or env vars
            "aws_secret_access_key": None,
            "endpoint_url": None,  # For S3-compatible services
            "encryption": True,
            "prefix": "tframex/",
            "batch_size": 100
        }
    
    elif storage_type == "redis":
        return {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": None,
            "ssl": False,
            "connection_pool_size": 10,
            "socket_timeout": 5,
            "retry_on_timeout": True,
            "health_check_interval": 30,
            "key_prefix": "tframex:",
            "ttl": {
                "sessions": 3600,  # 1 hour
                "temp_data": 300   # 5 minutes
            }
        }
    
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")


async def migrate_storage(
    source_type: str,
    source_config: Dict[str, Any],
    target_type: str,
    target_config: Dict[str, Any],
    tables: list = None
) -> None:
    """
    Migrate data from one storage backend to another.
    
    Args:
        source_type: Source storage type
        source_config: Source storage configuration
        target_type: Target storage type
        target_config: Target storage configuration
        tables: List of tables to migrate (None for all)
    """
    try:
        logger.info(f"Starting migration from {source_type} to {target_type}")
        
        # Create source and target storage
        source_storage = await create_storage_backend(source_type, source_config)
        target_storage = await create_storage_backend(target_type, target_config)
        
        try:
            # Get list of tables to migrate
            if tables is None:
                # Get all tables from source
                if hasattr(source_storage, 'list_tables'):
                    tables = await source_storage.list_tables()
                else:
                    # Default enterprise tables
                    tables = [
                        'users', 'roles', 'permissions', 'conversations', 
                        'messages', 'flow_executions', 'agent_executions',
                        'tool_calls', 'metrics', 'events', 'audit_logs'
                    ]
            
            # Migrate each table
            total_records = 0
            for table_name in tables:
                try:
                    logger.info(f"Migrating table: {table_name}")
                    
                    # Get all data from source
                    source_data = await source_storage.select(table_name)
                    
                    # Insert into target
                    for record in source_data:
                        await target_storage.insert(table_name, record)
                        total_records += 1
                    
                    logger.info(f"Migrated {len(source_data)} records from table {table_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to migrate table {table_name}: {e}")
                    # Continue with other tables
            
            logger.info(f"Migration completed successfully. Total records migrated: {total_records}")
            
        finally:
            # Clean up storage connections
            if hasattr(source_storage, 'close'):
                await source_storage.close()
            if hasattr(target_storage, 'close'):
                await target_storage.close()
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


class StorageRegistry:
    """
    Registry for custom storage backend implementations.
    """
    
    def __init__(self):
        self._storage_classes = {}
    
    def register(self, storage_type: str, storage_class):
        """
        Register a custom storage backend class.
        
        Args:
            storage_type: Storage type identifier
            storage_class: Storage class implementation
        """
        if not issubclass(storage_class, BaseStorage):
            raise ValueError("Storage class must inherit from BaseStorage")
        
        self._storage_classes[storage_type.lower()] = storage_class
        logger.info(f"Registered custom storage type: {storage_type}")
    
    def unregister(self, storage_type: str):
        """
        Unregister a storage backend type.
        
        Args:
            storage_type: Storage type to unregister
        """
        storage_type = storage_type.lower()
        if storage_type in self._storage_classes:
            del self._storage_classes[storage_type]
            logger.info(f"Unregistered storage type: {storage_type}")
    
    def get_class(self, storage_type: str):
        """
        Get storage class for a type.
        
        Args:
            storage_type: Storage type
            
        Returns:
            Storage class or None if not found
        """
        return self._storage_classes.get(storage_type.lower())
    
    def list_types(self) -> list:
        """Get list of registered storage types."""
        return list(self._storage_classes.keys())


# Global storage registry
storage_registry = StorageRegistry()


async def create_custom_storage_backend(
    storage_type: str, 
    config: Dict[str, Any]
) -> BaseStorage:
    """
    Create a custom storage backend using the registry.
    
    Args:
        storage_type: Custom storage type
        config: Storage configuration
        
    Returns:
        Storage backend instance
    """
    storage_class = storage_registry.get_class(storage_type)
    if not storage_class:
        raise ValueError(f"Custom storage type not registered: {storage_type}")
    
    storage = storage_class(config)
    await storage.initialize()
    return storage


# Enhanced factory function that supports custom storage types
async def create_storage_backend_with_registry(
    storage_type: str, 
    config: Dict[str, Any]
) -> BaseStorage:
    """
    Create storage backend with support for custom registered types.
    
    Args:
        storage_type: Storage type (built-in or custom)
        config: Storage configuration
        
    Returns:
        Storage backend instance
    """
    try:
        # Try built-in types first
        return await create_storage_backend(storage_type, config)
    except ValueError:
        # Try custom registered types
        return await create_custom_storage_backend(storage_type, config)