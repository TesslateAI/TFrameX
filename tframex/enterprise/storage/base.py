"""
Base Storage Interface

This module defines the abstract base class and interfaces for
all storage backend implementations.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Type
from uuid import UUID

from ..models import BaseModel

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass


class ConnectionError(StorageError):
    """Exception raised when storage connection fails."""
    pass


class QueryError(StorageError):
    """Exception raised when storage query fails."""
    pass


class ValidationError(StorageError):
    """Exception raised when data validation fails."""
    pass


class BaseStorage(ABC):
    """
    Abstract base class for all storage implementations.
    
    This class defines the interface that all storage backends must implement
    to provide consistent data persistence across different storage systems.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the storage backend.
        
        Args:
            config: Storage-specific configuration dictionary
        """
        self.config = config
        self._connected = False
        self._lock = asyncio.Lock()
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the storage backend.
        
        This method should be called after construction to set up
        the storage backend, create necessary tables, and establish
        initial connections.
        
        Raises:
            ConnectionError: If initialization fails
        """
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the storage backend.
        
        Raises:
            ConnectionError: If connection cannot be established
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close connection to the storage backend.
        """
        pass
    
    @abstractmethod
    async def ping(self) -> bool:
        """
        Test if the storage backend is accessible.
        
        Returns:
            True if storage is accessible, False otherwise
        """
        pass
    
    @abstractmethod
    async def create_table(self, table_name: str, schema: Dict[str, Any]) -> None:
        """
        Create a table with the given schema.
        
        Args:
            table_name: Name of the table to create
            schema: Table schema definition
            
        Raises:
            QueryError: If table creation fails
        """
        pass
    
    @abstractmethod
    async def insert(self, table_name: str, data: Dict[str, Any]) -> str:
        """
        Insert a record into the specified table.
        
        Args:
            table_name: Name of the table
            data: Record data to insert
            
        Returns:
            ID of the inserted record
            
        Raises:
            ValidationError: If data validation fails
            QueryError: If insert operation fails
        """
        pass
    
    @abstractmethod
    async def select(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Select records from the specified table.
        
        Args:
            table_name: Name of the table
            filters: Filter conditions as key-value pairs
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Field to order by
            order_desc: Whether to order in descending order
            
        Returns:
            List of matching records
            
        Raises:
            QueryError: If select operation fails
        """
        pass
    
    @abstractmethod
    async def update(
        self,
        table_name: str,
        record_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Update a record in the specified table.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to update
            data: Updated data
            
        Returns:
            True if record was updated, False if not found
            
        Raises:
            ValidationError: If data validation fails
            QueryError: If update operation fails
        """
        pass
    
    @abstractmethod
    async def delete(self, table_name: str, record_id: str) -> bool:
        """
        Delete a record from the specified table.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to delete
            
        Returns:
            True if record was deleted, False if not found
            
        Raises:
            QueryError: If delete operation fails
        """
        pass
    
    @abstractmethod
    async def count(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count records in the specified table.
        
        Args:
            table_name: Name of the table
            filters: Filter conditions as key-value pairs
            
        Returns:
            Number of matching records
            
        Raises:
            QueryError: If count operation fails
        """
        pass
    
    @abstractmethod
    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a raw query against the storage backend.
        
        Args:
            query: Raw query string
            params: Query parameters
            
        Returns:
            Query result
            
        Raises:
            QueryError: If query execution fails
        """
        pass
    
    # High-level model operations
    
    async def save_model(self, model: BaseModel, table_name: str) -> str:
        """
        Save a Pydantic model to storage.
        
        Args:
            model: Pydantic model instance
            table_name: Name of the table to save to
            
        Returns:
            ID of the saved record
        """
        try:
            data = model.model_dump(exclude_none=True)
            
            # Convert datetime objects to ISO strings
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                elif isinstance(value, UUID):
                    data[key] = str(value)
            
            return await self.insert(table_name, data)
        except Exception as e:
            logger.error(f"Failed to save model to {table_name}: {e}")
            raise QueryError(f"Failed to save model: {e}")
    
    async def load_model(
        self,
        model_class: Type[BaseModel],
        table_name: str,
        record_id: str
    ) -> Optional[BaseModel]:
        """
        Load a Pydantic model from storage.
        
        Args:
            model_class: Pydantic model class
            table_name: Name of the table to load from
            record_id: ID of the record to load
            
        Returns:
            Model instance or None if not found
        """
        try:
            records = await self.select(table_name, filters={"id": record_id})
            if not records:
                return None
            
            data = records[0]
            
            # Convert string UUIDs back to UUID objects
            for key, value in data.items():
                if isinstance(value, str) and key.endswith('_id') or key == 'id':
                    try:
                        data[key] = UUID(value)
                    except ValueError:
                        pass  # Not a valid UUID string
            
            return model_class.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to load model from {table_name}: {e}")
            raise QueryError(f"Failed to load model: {e}")
    
    async def load_models(
        self,
        model_class: Type[BaseModel],
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[BaseModel]:
        """
        Load multiple Pydantic models from storage.
        
        Args:
            model_class: Pydantic model class
            table_name: Name of the table to load from
            filters: Filter conditions
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Field to order by
            order_desc: Whether to order in descending order
            
        Returns:
            List of model instances
        """
        try:
            records = await self.select(
                table_name, filters, limit, offset, order_by, order_desc
            )
            
            models = []
            for data in records:
                # Convert string UUIDs back to UUID objects
                for key, value in data.items():
                    if isinstance(value, str) and (key.endswith('_id') or key == 'id'):
                        try:
                            data[key] = UUID(value)
                        except ValueError:
                            pass  # Not a valid UUID string
                
                models.append(model_class.model_validate(data))
            
            return models
        except Exception as e:
            logger.error(f"Failed to load models from {table_name}: {e}")
            raise QueryError(f"Failed to load models: {e}")
    
    async def update_model(
        self,
        model: BaseModel,
        table_name: str,
        record_id: str
    ) -> bool:
        """
        Update a Pydantic model in storage.
        
        Args:
            model: Updated Pydantic model instance
            table_name: Name of the table to update
            record_id: ID of the record to update
            
        Returns:
            True if record was updated, False if not found
        """
        try:
            data = model.model_dump(exclude_none=True)
            
            # Convert datetime objects to ISO strings
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                elif isinstance(value, UUID):
                    data[key] = str(value)
            
            # Add updated timestamp
            data['updated_at'] = datetime.utcnow().isoformat()
            
            return await self.update(table_name, record_id, data)
        except Exception as e:
            logger.error(f"Failed to update model in {table_name}: {e}")
            raise QueryError(f"Failed to update model: {e}")
    
    async def delete_model(self, table_name: str, record_id: str) -> bool:
        """
        Delete a model from storage.
        
        Args:
            table_name: Name of the table to delete from
            record_id: ID of the record to delete
            
        Returns:
            True if record was deleted, False if not found
        """
        try:
            return await self.delete(table_name, record_id)
        except Exception as e:
            logger.error(f"Failed to delete model from {table_name}: {e}")
            raise QueryError(f"Failed to delete model: {e}")
    
    # Transaction support (for backends that support it)
    
    async def begin_transaction(self) -> None:
        """Begin a transaction (if supported by backend)."""
        pass
    
    async def commit_transaction(self) -> None:
        """Commit the current transaction (if supported by backend)."""
        pass
    
    async def rollback_transaction(self) -> None:
        """Rollback the current transaction (if supported by backend)."""
        pass
    
    # Health and status
    
    @property
    def is_connected(self) -> bool:
        """Check if storage is connected."""
        return self._connected
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check.
        
        Returns:
            Health status information
        """
        try:
            ping_result = await self.ping()
            return {
                "connected": self._connected,
                "ping": ping_result,
                "backend": self.__class__.__name__,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "connected": False,
                "ping": False,
                "backend": self.__class__.__name__,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Context manager support
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()