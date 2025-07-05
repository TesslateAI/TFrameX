"""
SQLite Storage Implementation

This module provides a SQLite storage backend for single-node deployments
and development environments that need SQL persistence.
"""

import asyncio
import aiosqlite
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4, UUID

from .base import BaseStorage, ConnectionError, QueryError, ValidationError

logger = logging.getLogger(__name__)


def _serialize_for_json(obj):
    """
    Custom JSON serializer for datetime and UUID objects.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    else:
        return obj


class SQLiteStorage(BaseStorage):
    """
    SQLite storage implementation using aiosqlite for async operations.
    
    This storage backend is suitable for:
    - Single-node deployments
    - Development and testing with SQL persistence
    - Small to medium datasets
    - Scenarios where a full database server is not needed
    
    Features:
    - ACID transactions
    - File-based persistence
    - Full SQL query support
    - Lightweight and embedded
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SQLite storage.
        
        Args:
            config: Configuration dictionary with keys:
                - database_path: Path to SQLite database file
                - timeout: Connection timeout in seconds
                - check_same_thread: Whether to check thread safety
        """
        super().__init__(config)
        self.database_path = config.get("database_path", "tframex.db")
        self.timeout = config.get("timeout", 30.0)
        self.check_same_thread = config.get("check_same_thread", False)
        self._connection: Optional[aiosqlite.Connection] = None
        self._transaction_active = False
    
    async def initialize(self) -> None:
        """
        Initialize the SQLite storage backend.
        """
        await self.connect()
        logger.info("SQLite storage initialized")
    
    async def connect(self) -> None:
        """
        Establish connection to SQLite database.
        
        Creates the database file if it doesn't exist and enables
        foreign key constraints and WAL mode for better concurrency.
        """
        try:
            # Ensure database directory exists
            db_path = Path(self.database_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self._connection = await aiosqlite.connect(
                self.database_path,
                timeout=self.timeout,
                check_same_thread=self.check_same_thread
            )
            
            # Enable foreign key constraints
            await self._connection.execute("PRAGMA foreign_keys = ON")
            
            # Enable WAL mode for better concurrency
            await self._connection.execute("PRAGMA journal_mode = WAL")
            
            # Set synchronous mode for better performance
            await self._connection.execute("PRAGMA synchronous = NORMAL")
            
            await self._connection.commit()
            
            self._connected = True
            logger.info(f"Connected to SQLite database: {self.database_path}")
            
        except Exception as e:
            logger.error(f"Failed to connect to SQLite database: {e}")
            raise ConnectionError(f"Failed to connect to SQLite: {e}")
    
    async def disconnect(self) -> None:
        """
        Close connection to SQLite database.
        """
        if self._connection:
            try:
                if self._transaction_active:
                    await self.rollback_transaction()
                await self._connection.close()
                self._connected = False
                logger.info("Disconnected from SQLite database")
            except Exception as e:
                logger.error(f"Error during SQLite disconnect: {e}")
            finally:
                self._connection = None
    
    async def ping(self) -> bool:
        """
        Test if SQLite database is accessible.
        
        Returns:
            True if accessible, False otherwise
        """
        if not self._connected or not self._connection:
            return False
        
        try:
            cursor = await self._connection.execute("SELECT 1")
            await cursor.fetchone()
            await cursor.close()
            return True
        except Exception:
            return False
    
    async def create_table(self, table_name: str, schema: Dict[str, Any]) -> None:
        """
        Create a table with the given schema.
        
        Args:
            table_name: Name of the table to create
            schema: Table schema definition (currently uses default schema)
        """
        if not self._connection:
            raise ConnectionError("Not connected to database")
        
        try:
            # Create table with standard enterprise schema
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
            """
            
            await self._connection.execute(create_sql)
            
            # Create indexes for better performance
            await self._connection.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at)"
            )
            await self._connection.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_updated_at ON {table_name}(updated_at)"
            )
            
            if not self._transaction_active:
                await self._connection.commit()
            
            logger.debug(f"Created table: {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            raise QueryError(f"Failed to create table: {e}")
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> str:
        """
        Insert a record into the specified table.
        
        Args:
            table_name: Name of the table
            data: Record data to insert
            
        Returns:
            ID of the inserted record
        """
        if not self._connection:
            raise ConnectionError("Not connected to database")
        
        try:
            # Ensure table exists
            await self.create_table(table_name, {})
            
            # Generate ID if not provided
            record_data = dict(data)
            if 'id' not in record_data or not record_data['id']:
                record_data['id'] = str(uuid4())
            
            record_id = str(record_data['id'])
            
            # Add timestamps
            now = datetime.utcnow().isoformat()
            if 'created_at' not in record_data:
                record_data['created_at'] = now
            if 'updated_at' not in record_data:
                record_data['updated_at'] = now
            
            # Store data as JSON (with datetime serialization)
            serialized_data = _serialize_for_json(record_data)
            data_json = json.dumps(serialized_data)
            
            insert_sql = f"""
            INSERT INTO {table_name} (id, data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """
            
            await self._connection.execute(
                insert_sql,
                (record_id, data_json, record_data['created_at'], record_data['updated_at'])
            )
            
            if not self._transaction_active:
                await self._connection.commit()
            
            logger.debug(f"Inserted record {record_id} into {table_name}")
            return record_id
            
        except Exception as e:
            logger.error(f"Failed to insert into {table_name}: {e}")
            raise QueryError(f"Failed to insert record: {e}")
    
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
        if not self._connection:
            raise ConnectionError("Not connected to database")
        
        try:
            # Check if table exists
            cursor = await self._connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            if not await cursor.fetchone():
                await cursor.close()
                return []
            await cursor.close()
            
            # Build query
            query = f"SELECT data FROM {table_name}"
            params = []
            
            # Apply filters (basic filtering on JSON data)
            if filters:
                conditions = []
                for key, value in filters.items():
                    if key == 'id':
                        conditions.append("id = ?")
                        params.append(str(value))
                    else:
                        # For other fields, we need to extract from JSON
                        conditions.append(f"json_extract(data, '$.{key}') = ?")
                        params.append(value)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # Apply ordering
            if order_by:
                order_direction = "DESC" if order_desc else "ASC"
                if order_by in ['created_at', 'updated_at']:
                    query += f" ORDER BY {order_by} {order_direction}"
                else:
                    query += f" ORDER BY json_extract(data, '$.{order_by}') {order_direction}"
            
            # Apply pagination
            if limit:
                query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
            
            # Execute query
            cursor = await self._connection.execute(query, params)
            rows = await cursor.fetchall()
            await cursor.close()
            
            # Parse JSON data
            records = []
            for row in rows:
                try:
                    record = json.loads(row[0])
                    records.append(record)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON data: {e}")
                    continue
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to select from {table_name}: {e}")
            raise QueryError(f"Failed to select records: {e}")
    
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
        if not self._connection:
            raise ConnectionError("Not connected to database")
        
        try:
            # First, get the existing record
            existing_records = await self.select(table_name, {"id": record_id})
            if not existing_records:
                return False
            
            # Merge the data
            existing_data = existing_records[0]
            updated_data = {**existing_data, **data}
            updated_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update the record
            data_json = json.dumps(updated_data)
            update_sql = f"""
            UPDATE {table_name}
            SET data = ?, updated_at = ?
            WHERE id = ?
            """
            
            cursor = await self._connection.execute(
                update_sql,
                (data_json, updated_data['updated_at'], record_id)
            )
            
            updated = cursor.rowcount > 0
            await cursor.close()
            
            if not self._transaction_active:
                await self._connection.commit()
            
            if updated:
                logger.debug(f"Updated record {record_id} in {table_name}")
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to update record in {table_name}: {e}")
            raise QueryError(f"Failed to update record: {e}")
    
    async def delete(self, table_name: str, record_id: str) -> bool:
        """
        Delete a record from the specified table.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to delete
            
        Returns:
            True if record was deleted, False if not found
        """
        if not self._connection:
            raise ConnectionError("Not connected to database")
        
        try:
            delete_sql = f"DELETE FROM {table_name} WHERE id = ?"
            
            cursor = await self._connection.execute(delete_sql, (record_id,))
            deleted = cursor.rowcount > 0
            await cursor.close()
            
            if not self._transaction_active:
                await self._connection.commit()
            
            if deleted:
                logger.debug(f"Deleted record {record_id} from {table_name}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete from {table_name}: {e}")
            raise QueryError(f"Failed to delete record: {e}")
    
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
        if not self._connection:
            raise ConnectionError("Not connected to database")
        
        try:
            # Check if table exists
            cursor = await self._connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            if not await cursor.fetchone():
                await cursor.close()
                return 0
            await cursor.close()
            
            # Build count query
            query = f"SELECT COUNT(*) FROM {table_name}"
            params = []
            
            # Apply filters
            if filters:
                conditions = []
                for key, value in filters.items():
                    if key == 'id':
                        conditions.append("id = ?")
                        params.append(str(value))
                    else:
                        conditions.append(f"json_extract(data, '$.{key}') = ?")
                        params.append(value)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # Execute query
            cursor = await self._connection.execute(query, params)
            result = await cursor.fetchone()
            await cursor.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Failed to count records in {table_name}: {e}")
            raise QueryError(f"Failed to count records: {e}")
    
    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        if not self._connection:
            raise ConnectionError("Not connected to database")
        
        try:
            if params:
                cursor = await self._connection.execute(query, params)
            else:
                cursor = await self._connection.execute(query)
            
            # Determine if this is a SELECT query
            if query.strip().upper().startswith('SELECT'):
                result = await cursor.fetchall()
            else:
                result = cursor.rowcount
                if not self._transaction_active:
                    await self._connection.commit()
            
            await cursor.close()
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute raw query: {e}")
            raise QueryError(f"Failed to execute query: {e}")
    
    # Transaction support
    
    async def begin_transaction(self) -> None:
        """Begin a transaction."""
        if not self._connection:
            raise ConnectionError("Not connected to database")
        
        if self._transaction_active:
            raise QueryError("Transaction already active")
        
        try:
            await self._connection.execute("BEGIN")
            self._transaction_active = True
            logger.debug("Transaction started")
        except Exception as e:
            logger.error(f"Failed to begin transaction: {e}")
            raise QueryError(f"Failed to begin transaction: {e}")
    
    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        if not self._connection:
            raise ConnectionError("Not connected to database")
        
        if not self._transaction_active:
            raise QueryError("No active transaction")
        
        try:
            await self._connection.commit()
            self._transaction_active = False
            logger.debug("Transaction committed")
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            self._transaction_active = False
            raise QueryError(f"Failed to commit transaction: {e}")
    
    async def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        if not self._connection:
            raise ConnectionError("Not connected to database")
        
        if not self._transaction_active:
            raise QueryError("No active transaction")
        
        try:
            await self._connection.rollback()
            self._transaction_active = False
            logger.debug("Transaction rolled back")
        except Exception as e:
            logger.error(f"Failed to rollback transaction: {e}")
            self._transaction_active = False
            raise QueryError(f"Failed to rollback transaction: {e}")
    
    # SQLite-specific utilities
    
    async def vacuum(self) -> None:
        """
        Vacuum the database to reclaim space and optimize performance.
        """
        if not self._connection:
            raise ConnectionError("Not connected to database")
        
        try:
            await self._connection.execute("VACUUM")
            logger.info("Database vacuumed successfully")
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
            raise QueryError(f"Failed to vacuum database: {e}")
    
    async def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the SQLite database.
        
        Returns:
            Database information including size, page count, etc.
        """
        if not self._connection:
            raise ConnectionError("Not connected to database")
        
        try:
            info = {}
            
            # Get database size
            db_path = Path(self.database_path)
            if db_path.exists():
                info['file_size_bytes'] = db_path.stat().st_size
            
            # Get page count and page size
            cursor = await self._connection.execute("PRAGMA page_count")
            page_count = await cursor.fetchone()
            await cursor.close()
            
            cursor = await self._connection.execute("PRAGMA page_size")
            page_size = await cursor.fetchone()
            await cursor.close()
            
            info['page_count'] = page_count[0] if page_count else 0
            info['page_size'] = page_size[0] if page_size else 0
            
            # Get table list
            cursor = await self._connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = await cursor.fetchall()
            await cursor.close()
            
            info['tables'] = [table[0] for table in tables]
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            raise QueryError(f"Failed to get database info: {e}")