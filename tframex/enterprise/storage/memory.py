"""
In-Memory Storage Implementation

This module provides an in-memory storage backend for development
and testing purposes. Data is stored in Python dictionaries and
is not persisted between application restarts.
"""

import asyncio
import copy
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .base import BaseStorage, QueryError, ValidationError

logger = logging.getLogger(__name__)


class InMemoryStorage(BaseStorage):
    """
    In-memory storage implementation using Python dictionaries.
    
    This storage backend keeps all data in memory and is suitable for:
    - Development and testing
    - Small datasets that fit in memory
    - Scenarios where data persistence is not required
    
    Data is organized as tables (dictionaries) containing records (dictionaries).
    Each record must have an 'id' field that serves as the primary key.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize in-memory storage.
        
        Args:
            config: Configuration dictionary (unused for memory backend)
        """
        super().__init__(config)
        self._tables: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """
        Initialize the in-memory storage backend.
        """
        await self.connect()
        logger.info("In-memory storage initialized")
    
    async def connect(self) -> None:
        """
        Establish connection (no-op for memory backend).
        """
        async with self._lock:
            self._connected = True
            logger.info("Connected to in-memory storage")
    
    async def disconnect(self) -> None:
        """
        Close connection and clear all data.
        """
        async with self._lock:
            self._tables.clear()
            self._schemas.clear()
            self._connected = False
            logger.info("Disconnected from in-memory storage")
    
    async def ping(self) -> bool:
        """
        Test if storage is accessible.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connected
    
    async def create_table(self, table_name: str, schema: Dict[str, Any]) -> None:
        """
        Create a table with the given schema.
        
        Args:
            table_name: Name of the table to create
            schema: Table schema definition
        """
        async with self._lock:
            if table_name not in self._tables:
                self._tables[table_name] = {}
                self._schemas[table_name] = schema
                logger.debug(f"Created table: {table_name}")
            else:
                logger.debug(f"Table already exists: {table_name}")
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> str:
        """
        Insert a record into the specified table.
        
        Args:
            table_name: Name of the table
            data: Record data to insert
            
        Returns:
            ID of the inserted record
        """
        async with self._lock:
            # Ensure table exists (without re-acquiring lock)
            if table_name not in self._tables:
                self._tables[table_name] = {}
                self._schemas[table_name] = {}
                logger.debug(f"Created table: {table_name}")
            
            # Generate ID if not provided
            record_data = copy.deepcopy(data)
            if 'id' not in record_data or not record_data['id']:
                record_data['id'] = str(uuid4())
            
            record_id = str(record_data['id'])
            
            # Validate that ID doesn't already exist
            if record_id in self._tables[table_name]:
                raise ValidationError(f"Record with ID {record_id} already exists")
            
            # Add timestamps
            now = datetime.utcnow().isoformat()
            if 'created_at' not in record_data:
                record_data['created_at'] = now
            if 'updated_at' not in record_data:
                record_data['updated_at'] = now
            
            # Store the record
            self._tables[table_name][record_id] = record_data
            
            logger.debug(f"Inserted record {record_id} into {table_name}")
            return record_id
    
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
        """
        async with self._lock:
            if table_name not in self._tables:
                return []
            
            records = list(self._tables[table_name].values())
            
            # Apply filters
            if filters:
                filtered_records = []
                for record in records:
                    match = True
                    for key, value in filters.items():
                        if key not in record or record[key] != value:
                            match = False
                            break
                    if match:
                        filtered_records.append(record)
                records = filtered_records
            
            # Apply ordering
            if order_by and records:
                try:
                    records.sort(
                        key=lambda x: x.get(order_by, ''),
                        reverse=order_desc
                    )
                except (TypeError, KeyError):
                    logger.warning(f"Could not sort by {order_by}")
            
            # Apply pagination
            if offset:
                records = records[offset:]
            if limit:
                records = records[:limit]
            
            # Return deep copies to prevent external modifications
            return [copy.deepcopy(record) for record in records]
    
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
        """
        async with self._lock:
            if table_name not in self._tables:
                return False
            
            if record_id not in self._tables[table_name]:
                return False
            
            # Update the record
            record = self._tables[table_name][record_id]
            for key, value in data.items():
                if key != 'id':  # Prevent ID modification
                    record[key] = value
            
            # Update timestamp
            record['updated_at'] = datetime.utcnow().isoformat()
            
            logger.debug(f"Updated record {record_id} in {table_name}")
            return True
    
    async def delete(self, table_name: str, record_id: str) -> bool:
        """
        Delete a record from the specified table.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to delete
            
        Returns:
            True if record was deleted, False if not found
        """
        async with self._lock:
            if table_name not in self._tables:
                return False
            
            if record_id not in self._tables[table_name]:
                return False
            
            del self._tables[table_name][record_id]
            logger.debug(f"Deleted record {record_id} from {table_name}")
            return True
    
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
        """
        records = await self.select(table_name, filters)
        return len(records)
    
    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a raw query (not supported for memory backend).
        
        Args:
            query: Raw query string
            params: Query parameters
            
        Returns:
            None
            
        Raises:
            QueryError: Always raised as raw queries are not supported
        """
        raise QueryError("Raw queries are not supported by in-memory storage")
    
    # Additional methods specific to memory backend
    
    async def clear_table(self, table_name: str) -> None:
        """
        Clear all records from a table.
        
        Args:
            table_name: Name of the table to clear
        """
        async with self._lock:
            if table_name in self._tables:
                self._tables[table_name].clear()
                logger.debug(f"Cleared table: {table_name}")
    
    async def drop_table(self, table_name: str) -> None:
        """
        Drop a table and all its data.
        
        Args:
            table_name: Name of the table to drop
        """
        async with self._lock:
            if table_name in self._tables:
                del self._tables[table_name]
                if table_name in self._schemas:
                    del self._schemas[table_name]
                logger.debug(f"Dropped table: {table_name}")
    
    async def list_tables(self) -> List[str]:
        """
        List all table names.
        
        Returns:
            List of table names
        """
        async with self._lock:
            return list(self._tables.keys())
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table information including record count and schema
        """
        async with self._lock:
            if table_name not in self._tables:
                return {"exists": False}
            
            return {
                "exists": True,
                "record_count": len(self._tables[table_name]),
                "schema": self._schemas.get(table_name, {}),
                "sample_record": (
                    list(self._tables[table_name].values())[0]
                    if self._tables[table_name]
                    else None
                )
            }
    
    # Bulk operations for better performance
    
    async def bulk_insert(self, table_name: str, records: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple records in a single operation.
        
        Args:
            table_name: Name of the table
            records: List of records to insert
            
        Returns:
            List of inserted record IDs
        """
        async with self._lock:
            # Ensure table exists
            if table_name not in self._tables:
                await self.create_table(table_name, {})
            
            inserted_ids = []
            now = datetime.utcnow().isoformat()
            
            for record_data in records:
                record_data = copy.deepcopy(record_data)
                
                # Generate ID if not provided
                if 'id' not in record_data or not record_data['id']:
                    record_data['id'] = str(uuid4())
                
                record_id = str(record_data['id'])
                
                # Validate that ID doesn't already exist
                if record_id in self._tables[table_name]:
                    raise ValidationError(f"Record with ID {record_id} already exists")
                
                # Add timestamps
                if 'created_at' not in record_data:
                    record_data['created_at'] = now
                if 'updated_at' not in record_data:
                    record_data['updated_at'] = now
                
                # Store the record
                self._tables[table_name][record_id] = record_data
                inserted_ids.append(record_id)
            
            logger.debug(f"Bulk inserted {len(inserted_ids)} records into {table_name}")
            return inserted_ids
    
    async def export_data(self) -> Dict[str, Any]:
        """
        Export all data for backup or migration.
        
        Returns:
            Dictionary containing all tables and their data
        """
        async with self._lock:
            return {
                "tables": copy.deepcopy(self._tables),
                "schemas": copy.deepcopy(self._schemas),
                "exported_at": datetime.utcnow().isoformat()
            }
    
    async def import_data(self, data: Dict[str, Any]) -> None:
        """
        Import data from backup or migration.
        
        Args:
            data: Data dictionary to import
        """
        async with self._lock:
            if "tables" in data:
                self._tables = copy.deepcopy(data["tables"])
            if "schemas" in data:
                self._schemas = copy.deepcopy(data["schemas"])
            logger.info("Imported data into in-memory storage")