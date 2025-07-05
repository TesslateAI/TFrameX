"""
PostgreSQL Storage Implementation

This module provides a PostgreSQL storage backend for production deployments
with full SQL capabilities, ACID transactions, and scalability.
"""

import asyncio
import asyncpg
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from .base import BaseStorage, ConnectionError, QueryError, ValidationError

logger = logging.getLogger(__name__)


class PostgreSQLStorage(BaseStorage):
    """
    PostgreSQL storage implementation using asyncpg for high performance.
    
    This storage backend is suitable for:
    - Production deployments
    - High-performance applications
    - Multi-user environments
    - Large datasets requiring SQL queries
    - Applications requiring ACID transactions
    
    Features:
    - Full ACID compliance
    - Connection pooling
    - Advanced SQL features
    - JSON/JSONB support
    - High concurrency
    - Backup and replication support
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PostgreSQL storage.
        
        Args:
            config: Configuration dictionary with keys:
                - connection_string: PostgreSQL connection string
                - pool_size: Maximum number of connections in pool
                - max_overflow: Maximum additional connections
                - pool_timeout: Connection timeout in seconds
                - command_timeout: Query timeout in seconds
        """
        super().__init__(config)
        self.connection_string = config.get("connection_string")
        self.pool_size = config.get("pool_size", 10)
        self.max_overflow = config.get("max_overflow", 20)
        self.pool_timeout = config.get("pool_timeout", 30)
        self.command_timeout = config.get("command_timeout", 60)
        
        self._pool: Optional[asyncpg.Pool] = None
        self._transaction_connection: Optional[asyncpg.Connection] = None
        self._transaction_active = False
        
        if not self.connection_string:
            raise ValueError("PostgreSQL connection_string is required")
    
    async def initialize(self) -> None:
        """
        Initialize the PostgreSQL storage backend.
        """
        await self.connect()
        logger.info("PostgreSQL storage initialized")
    
    async def connect(self) -> None:
        """
        Establish connection pool to PostgreSQL database.
        """
        try:
            self._pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=1,
                max_size=self.pool_size,
                command_timeout=self.command_timeout
            )
            
            # Test the connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            self._connected = True
            logger.info("Connected to PostgreSQL database")
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")
    
    async def disconnect(self) -> None:
        """
        Close connection pool.
        """
        if self._pool:
            try:
                if self._transaction_active and self._transaction_connection:
                    await self.rollback_transaction()
                
                await self._pool.close()
                self._connected = False
                logger.info("Disconnected from PostgreSQL database")
            except Exception as e:
                logger.error(f"Error during PostgreSQL disconnect: {e}")
            finally:
                self._pool = None
    
    async def ping(self) -> bool:
        """
        Test if PostgreSQL database is accessible.
        
        Returns:
            True if accessible, False otherwise
        """
        if not self._connected or not self._pool:
            return False
        
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
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
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        try:
            conn = self._transaction_connection if self._transaction_active else None
            
            if conn:
                await self._create_table_with_connection(conn, table_name)
            else:
                async with self._pool.acquire() as conn:
                    await self._create_table_with_connection(conn, table_name)
            
            logger.debug(f"Created table: {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            raise QueryError(f"Failed to create table: {e}")
    
    async def _create_table_with_connection(self, conn: asyncpg.Connection, table_name: str) -> None:
        """Create table using provided connection."""
        # Create table with JSONB for better performance
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            data JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
        
        await conn.execute(create_sql)
        
        # Create indexes for better performance
        await conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at)"
        )
        await conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_updated_at ON {table_name}(updated_at)"
        )
        
        # Create GIN index on JSONB data for fast queries
        await conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_data_gin ON {table_name} USING GIN (data)"
        )
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> str:
        """
        Insert a record into the specified table.
        
        Args:
            table_name: Name of the table
            data: Record data to insert
            
        Returns:
            ID of the inserted record
        """
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        try:
            # Ensure table exists
            await self.create_table(table_name, {})
            
            # Prepare data
            record_data = dict(data)
            if 'id' not in record_data or not record_data['id']:
                record_data['id'] = str(uuid4())
            
            record_id = str(record_data['id'])
            
            # Add timestamps
            now = datetime.utcnow()
            if 'created_at' not in record_data:
                record_data['created_at'] = now.isoformat()
            if 'updated_at' not in record_data:
                record_data['updated_at'] = now.isoformat()
            
            # Insert the record
            insert_sql = f"""
            INSERT INTO {table_name} (id, data, created_at, updated_at)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """
            
            conn = self._transaction_connection if self._transaction_active else None
            
            if conn:
                result = await conn.fetchval(
                    insert_sql,
                    record_id, json.dumps(record_data), now, now
                )
            else:
                async with self._pool.acquire() as conn:
                    result = await conn.fetchval(
                        insert_sql,
                        record_id, json.dumps(record_data), now, now
                    )
            
            logger.debug(f"Inserted record {record_id} into {table_name}")
            return str(result)
            
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
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        try:
            # Check if table exists
            conn = self._transaction_connection if self._transaction_active else None
            
            if conn:
                exists = await self._check_table_exists(conn, table_name)
            else:
                async with self._pool.acquire() as conn:
                    exists = await self._check_table_exists(conn, table_name)
            
            if not exists:
                return []
            
            # Build query
            query = f"SELECT data FROM {table_name}"
            params = []
            param_count = 0
            
            # Apply filters
            if filters:
                conditions = []
                for key, value in filters.items():
                    param_count += 1
                    if key == 'id':
                        conditions.append(f"id = ${param_count}")
                        params.append(value)
                    else:
                        # Use JSONB operators for efficient querying
                        conditions.append(f"data->>'{key}' = ${param_count}")
                        params.append(str(value))
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # Apply ordering
            if order_by:
                order_direction = "DESC" if order_desc else "ASC"
                if order_by in ['created_at', 'updated_at']:
                    query += f" ORDER BY {order_by} {order_direction}"
                else:
                    query += f" ORDER BY data->>'{order_by}' {order_direction}"
            
            # Apply pagination
            if limit:
                param_count += 1
                query += f" LIMIT ${param_count}"
                params.append(limit)
            
            if offset:
                param_count += 1
                query += f" OFFSET ${param_count}"
                params.append(offset)
            
            # Execute query
            if conn:
                rows = await conn.fetch(query, *params)
            else:
                async with self._pool.acquire() as conn:
                    rows = await conn.fetch(query, *params)
            
            # Parse JSON data
            records = []
            for row in rows:
                try:
                    if isinstance(row['data'], str):
                        record = json.loads(row['data'])
                    else:
                        record = dict(row['data'])
                    records.append(record)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse JSON data: {e}")
                    continue
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to select from {table_name}: {e}")
            raise QueryError(f"Failed to select records: {e}")
    
    async def _check_table_exists(self, conn: asyncpg.Connection, table_name: str) -> bool:
        """Check if table exists."""
        result = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = $1)",
            table_name
        )
        return result
    
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
        if not self._pool:
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
            update_sql = f"""
            UPDATE {table_name}
            SET data = $1, updated_at = $2
            WHERE id = $3
            """
            
            conn = self._transaction_connection if self._transaction_active else None
            
            if conn:
                result = await conn.execute(
                    update_sql,
                    json.dumps(updated_data), datetime.utcnow(), record_id
                )
            else:
                async with self._pool.acquire() as conn:
                    result = await conn.execute(
                        update_sql,
                        json.dumps(updated_data), datetime.utcnow(), record_id
                    )
            
            # Check if any rows were updated
            updated = result.split()[-1] != '0'
            
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
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        try:
            delete_sql = f"DELETE FROM {table_name} WHERE id = $1"
            
            conn = self._transaction_connection if self._transaction_active else None
            
            if conn:
                result = await conn.execute(delete_sql, record_id)
            else:
                async with self._pool.acquire() as conn:
                    result = await conn.execute(delete_sql, record_id)
            
            # Check if any rows were deleted
            deleted = result.split()[-1] != '0'
            
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
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        try:
            # Check if table exists
            conn = self._transaction_connection if self._transaction_active else None
            
            if conn:
                exists = await self._check_table_exists(conn, table_name)
            else:
                async with self._pool.acquire() as conn:
                    exists = await self._check_table_exists(conn, table_name)
            
            if not exists:
                return 0
            
            # Build count query
            query = f"SELECT COUNT(*) FROM {table_name}"
            params = []
            param_count = 0
            
            # Apply filters
            if filters:
                conditions = []
                for key, value in filters.items():
                    param_count += 1
                    if key == 'id':
                        conditions.append(f"id = ${param_count}")
                        params.append(value)
                    else:
                        conditions.append(f"data->>'{key}' = ${param_count}")
                        params.append(str(value))
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # Execute query
            if conn:
                result = await conn.fetchval(query, *params)
            else:
                async with self._pool.acquire() as conn:
                    result = await conn.fetchval(query, *params)
            
            return result or 0
            
        except Exception as e:
            logger.error(f"Failed to count records in {table_name}: {e}")
            raise QueryError(f"Failed to count records: {e}")
    
    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters (positional list for PostgreSQL)
            
        Returns:
            Query result
        """
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        try:
            conn = self._transaction_connection if self._transaction_active else None
            
            if conn:
                if query.strip().upper().startswith('SELECT'):
                    result = await conn.fetch(query, *(params or []))
                else:
                    result = await conn.execute(query, *(params or []))
            else:
                async with self._pool.acquire() as conn:
                    if query.strip().upper().startswith('SELECT'):
                        result = await conn.fetch(query, *(params or []))
                    else:
                        result = await conn.execute(query, *(params or []))
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute raw query: {e}")
            raise QueryError(f"Failed to execute query: {e}")
    
    # Transaction support
    
    async def begin_transaction(self) -> None:
        """Begin a transaction."""
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        if self._transaction_active:
            raise QueryError("Transaction already active")
        
        try:
            self._transaction_connection = await self._pool.acquire()
            self._transaction = self._transaction_connection.transaction()
            await self._transaction.start()
            self._transaction_active = True
            logger.debug("Transaction started")
        except Exception as e:
            if self._transaction_connection:
                await self._pool.release(self._transaction_connection)
                self._transaction_connection = None
            logger.error(f"Failed to begin transaction: {e}")
            raise QueryError(f"Failed to begin transaction: {e}")
    
    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        if not self._transaction_active or not self._transaction_connection:
            raise QueryError("No active transaction")
        
        try:
            await self._transaction.commit()
            await self._pool.release(self._transaction_connection)
            self._transaction_connection = None
            self._transaction = None
            self._transaction_active = False
            logger.debug("Transaction committed")
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            await self.rollback_transaction()
            raise QueryError(f"Failed to commit transaction: {e}")
    
    async def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        if not self._transaction_active or not self._transaction_connection:
            raise QueryError("No active transaction")
        
        try:
            await self._transaction.rollback()
            await self._pool.release(self._transaction_connection)
            self._transaction_connection = None
            self._transaction = None
            self._transaction_active = False
            logger.debug("Transaction rolled back")
        except Exception as e:
            logger.error(f"Failed to rollback transaction: {e}")
            self._transaction_connection = None
            self._transaction = None
            self._transaction_active = False
            raise QueryError(f"Failed to rollback transaction: {e}")
    
    # PostgreSQL-specific utilities
    
    async def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the PostgreSQL database.
        
        Returns:
            Database information
        """
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        try:
            async with self._pool.acquire() as conn:
                # Get database version
                version = await conn.fetchval("SELECT version()")
                
                # Get database size
                db_name = await conn.fetchval("SELECT current_database()")
                db_size = await conn.fetchval(
                    "SELECT pg_size_pretty(pg_database_size($1))", db_name
                )
                
                # Get table list
                tables = await conn.fetch(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                )
                
                # Get connection info
                pool_info = {
                    "pool_size": self._pool.get_size(),
                    "pool_max_size": self._pool.get_max_size(),
                    "pool_min_size": self._pool.get_min_size()
                }
                
                return {
                    "version": version,
                    "database_name": db_name,
                    "database_size": db_size,
                    "tables": [table['tablename'] for table in tables],
                    "pool_info": pool_info
                }
                
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            raise QueryError(f"Failed to get database info: {e}")
    
    async def analyze_table(self, table_name: str) -> None:
        """
        Analyze a table to update statistics for query optimization.
        
        Args:
            table_name: Name of the table to analyze
        """
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(f"ANALYZE {table_name}")
            logger.info(f"Analyzed table: {table_name}")
        except Exception as e:
            logger.error(f"Failed to analyze table {table_name}: {e}")
            raise QueryError(f"Failed to analyze table: {e}")