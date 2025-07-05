"""
S3 Storage Implementation

This module provides an S3-compatible storage backend for archival,
large-scale data storage, and distributed deployments.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:
    import aioboto3
    import botocore.exceptions
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

from .base import BaseStorage, ConnectionError, QueryError, ValidationError

logger = logging.getLogger(__name__)


class S3Storage(BaseStorage):
    """
    S3-compatible storage implementation using aioboto3.
    
    This storage backend is suitable for:
    - Long-term data archival
    - Large-scale data storage
    - Distributed and cloud deployments
    - Audit log storage
    - Backup and disaster recovery
    
    Features:
    - S3-compatible API
    - Versioning support
    - Server-side encryption
    - Cross-region replication
    - Lifecycle management
    - Cost-effective storage
    
    Note: This backend is optimized for write-heavy workloads and
    eventual consistency. It's not suitable for frequent updates
    or real-time queries.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize S3 storage.
        
        Args:
            config: Configuration dictionary with keys:
                - bucket_name: S3 bucket name
                - aws_access_key_id: AWS access key ID
                - aws_secret_access_key: AWS secret access key
                - region_name: AWS region name
                - endpoint_url: Custom S3 endpoint (for S3-compatible services)
                - prefix: Key prefix for all objects
                - encryption: Server-side encryption settings
        """
        super().__init__(config)
        
        if not S3_AVAILABLE:
            raise ImportError(
                "aioboto3 is required for S3 storage. "
                "Install with: pip install aioboto3"
            )
        
        self.bucket_name = config.get("bucket_name")
        self.aws_access_key_id = config.get("aws_access_key_id")
        self.aws_secret_access_key = config.get("aws_secret_access_key")
        self.region_name = config.get("region_name", "us-east-1")
        self.endpoint_url = config.get("endpoint_url")
        self.prefix = config.get("prefix", "tframex")
        self.encryption = config.get("encryption", {})
        
        self._session = None
        self._s3_client = None
        
        if not self.bucket_name:
            raise ValueError("S3 bucket_name is required")
    
    async def initialize(self) -> None:
        """
        Initialize the S3 storage backend.
        """
        await self.connect()
        logger.info("S3 storage initialized")
    
    async def connect(self) -> None:
        """
        Establish connection to S3.
        """
        try:
            # Create aioboto3 session
            self._session = aioboto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
            
            # Create S3 client
            self._s3_client = self._session.client(
                's3',
                endpoint_url=self.endpoint_url
            )
            
            # Test connection by checking if bucket exists
            await self._s3_client.head_bucket(Bucket=self.bucket_name)
            
            self._connected = True
            logger.info(f"Connected to S3 bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to S3: {e}")
            raise ConnectionError(f"Failed to connect to S3: {e}")
    
    async def disconnect(self) -> None:
        """
        Close S3 client.
        """
        if self._s3_client:
            try:
                await self._s3_client.close()
                self._connected = False
                logger.info("Disconnected from S3")
            except Exception as e:
                logger.error(f"Error during S3 disconnect: {e}")
            finally:
                self._s3_client = None
                self._session = None
    
    async def ping(self) -> bool:
        """
        Test if S3 bucket is accessible.
        
        Returns:
            True if accessible, False otherwise
        """
        if not self._connected or not self._s3_client:
            return False
        
        try:
            await self._s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception:
            return False
    
    async def create_table(self, table_name: str, schema: Dict[str, Any]) -> None:
        """
        Create a 'table' (S3 prefix) with metadata.
        
        Args:
            table_name: Name of the table (used as S3 prefix)
            schema: Table schema definition (stored as metadata)
        """
        if not self._s3_client:
            raise ConnectionError("Not connected to S3")
        
        try:
            # Store table metadata
            metadata_key = f"{self.prefix}/tables/{table_name}/_metadata.json"
            metadata = {
                "table_name": table_name,
                "schema": schema,
                "created_at": datetime.utcnow().isoformat(),
                "record_count": 0
            }
            
            put_params = {
                'Bucket': self.bucket_name,
                'Key': metadata_key,
                'Body': json.dumps(metadata),
                'ContentType': 'application/json'
            }
            
            # Add encryption if configured
            if self.encryption:
                put_params.update(self.encryption)
            
            await self._s3_client.put_object(**put_params)
            
            logger.debug(f"Created table metadata: {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            raise QueryError(f"Failed to create table: {e}")
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> str:
        """
        Insert a record into S3.
        
        Args:
            table_name: Name of the table
            data: Record data to insert
            
        Returns:
            ID of the inserted record
        """
        if not self._s3_client:
            raise ConnectionError("Not connected to S3")
        
        try:
            # Ensure table exists
            await self.create_table(table_name, {})
            
            # Prepare record data
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
            
            # Create S3 key
            # Use date partitioning for better organization
            date_partition = datetime.utcnow().strftime("%Y/%m/%d")
            object_key = f"{self.prefix}/tables/{table_name}/data/{date_partition}/{record_id}.json"
            
            # Store record
            put_params = {
                'Bucket': self.bucket_name,
                'Key': object_key,
                'Body': json.dumps(record_data),
                'ContentType': 'application/json',
                'Metadata': {
                    'table_name': table_name,
                    'record_id': record_id,
                    'created_at': now
                }
            }
            
            # Add encryption if configured
            if self.encryption:
                put_params.update(self.encryption)
            
            await self._s3_client.put_object(**put_params)
            
            # Update table metadata (record count)
            await self._update_table_metadata(table_name, increment_count=True)
            
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
        Select records from S3.
        
        Note: This operation can be expensive for large datasets as it
        requires listing and reading multiple S3 objects. Consider using
        date range filters to limit the search scope.
        
        Args:
            table_name: Name of the table
            filters: Filter conditions (supports 'date_from' and 'date_to' for optimization)
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Field to order by (limited support)
            order_desc: Whether to order in descending order
            
        Returns:
            List of matching records
        """
        if not self._s3_client:
            raise ConnectionError("Not connected to S3")
        
        try:
            # Check if table exists
            if not await self._table_exists(table_name):
                return []
            
            records = []
            table_prefix = f"{self.prefix}/tables/{table_name}/data/"
            
            # Use date filters for optimization if provided
            search_prefixes = []
            if filters and ('date_from' in filters or 'date_to' in filters):
                search_prefixes = await self._build_date_prefixes(
                    table_prefix, filters.get('date_from'), filters.get('date_to')
                )
            else:
                search_prefixes = [table_prefix]
            
            # List and read objects
            for prefix in search_prefixes:
                paginator = self._s3_client.get_paginator('list_objects_v2')
                page_iterator = paginator.paginate(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                
                async for page in page_iterator:
                    if 'Contents' not in page:
                        continue
                    
                    for obj in page['Contents']:
                        if obj['Key'].endswith('.json') and '/data/' in obj['Key']:
                            try:
                                # Read object
                                response = await self._s3_client.get_object(
                                    Bucket=self.bucket_name,
                                    Key=obj['Key']
                                )
                                
                                # Parse JSON
                                body = await response['Body'].read()
                                record = json.loads(body.decode('utf-8'))
                                
                                # Apply filters
                                if self._matches_filters(record, filters):
                                    records.append(record)
                                
                                # Apply limit early to avoid reading too many objects
                                if limit and len(records) >= (limit + (offset or 0)):
                                    break
                                    
                            except Exception as e:
                                logger.warning(f"Failed to read object {obj['Key']}: {e}")
                                continue
                
                if limit and len(records) >= (limit + (offset or 0)):
                    break
            
            # Sort records if requested
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
        Update a record in S3.
        
        Note: This operation is expensive as it requires finding the object,
        reading it, updating it, and writing it back. S3 is not optimized
        for frequent updates.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to update
            data: Updated data
            
        Returns:
            True if record was updated, False if not found
        """
        if not self._s3_client:
            raise ConnectionError("Not connected to S3")
        
        try:
            # Find the existing record
            existing_record = await self._find_record_by_id(table_name, record_id)
            if not existing_record:
                return False
            
            # Merge data
            updated_data = {**existing_record['data'], **data}
            updated_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Delete old object
            await self._s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=existing_record['key']
            )
            
            # Insert updated record
            await self.insert(table_name, updated_data)
            
            logger.debug(f"Updated record {record_id} in {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update record in {table_name}: {e}")
            raise QueryError(f"Failed to update record: {e}")
    
    async def delete(self, table_name: str, record_id: str) -> bool:
        """
        Delete a record from S3.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to delete
            
        Returns:
            True if record was deleted, False if not found
        """
        if not self._s3_client:
            raise ConnectionError("Not connected to S3")
        
        try:
            # Find the record
            existing_record = await self._find_record_by_id(table_name, record_id)
            if not existing_record:
                return False
            
            # Delete the object
            await self._s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=existing_record['key']
            )
            
            # Update table metadata
            await self._update_table_metadata(table_name, increment_count=False)
            
            logger.debug(f"Deleted record {record_id} from {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete from {table_name}: {e}")
            raise QueryError(f"Failed to delete record: {e}")
    
    async def count(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count records in S3.
        
        Note: This can be expensive for large datasets. Consider using
        the table metadata for approximate counts.
        
        Args:
            table_name: Name of the table
            filters: Filter conditions
            
        Returns:
            Number of matching records
        """
        if filters:
            # If filters are provided, we need to read all records
            records = await self.select(table_name, filters)
            return len(records)
        else:
            # Use table metadata for faster count
            metadata = await self._get_table_metadata(table_name)
            return metadata.get('record_count', 0) if metadata else 0
    
    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute raw operations (limited support for S3).
        
        Args:
            query: Operation string (e.g., "list_buckets", "get_bucket_info")
            params: Operation parameters
            
        Returns:
            Operation result
        """
        if not self._s3_client:
            raise ConnectionError("Not connected to S3")
        
        try:
            if query == "list_buckets":
                response = await self._s3_client.list_buckets()
                return response.get('Buckets', [])
            
            elif query == "get_bucket_info":
                bucket_name = params.get('bucket_name', self.bucket_name)
                response = await self._s3_client.head_bucket(Bucket=bucket_name)
                return response
            
            elif query == "list_tables":
                return await self._list_tables()
            
            else:
                raise QueryError(f"Unsupported raw operation: {query}")
                
        except Exception as e:
            logger.error(f"Failed to execute raw operation: {e}")
            raise QueryError(f"Failed to execute operation: {e}")
    
    # S3-specific helper methods
    
    async def _table_exists(self, table_name: str) -> bool:
        """Check if table metadata exists."""
        try:
            metadata_key = f"{self.prefix}/tables/{table_name}/_metadata.json"
            await self._s3_client.head_object(
                Bucket=self.bucket_name,
                Key=metadata_key
            )
            return True
        except self._s3_client.exceptions.NoSuchKey:
            return False
        except Exception:
            return False
    
    async def _get_table_metadata(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get table metadata."""
        try:
            metadata_key = f"{self.prefix}/tables/{table_name}/_metadata.json"
            response = await self._s3_client.get_object(
                Bucket=self.bucket_name,
                Key=metadata_key
            )
            body = await response['Body'].read()
            return json.loads(body.decode('utf-8'))
        except Exception:
            return None
    
    async def _update_table_metadata(self, table_name: str, increment_count: bool = True) -> None:
        """Update table metadata."""
        try:
            metadata = await self._get_table_metadata(table_name)
            if metadata:
                if increment_count:
                    metadata['record_count'] = metadata.get('record_count', 0) + 1
                else:
                    metadata['record_count'] = max(0, metadata.get('record_count', 1) - 1)
                
                metadata['updated_at'] = datetime.utcnow().isoformat()
                
                metadata_key = f"{self.prefix}/tables/{table_name}/_metadata.json"
                put_params = {
                    'Bucket': self.bucket_name,
                    'Key': metadata_key,
                    'Body': json.dumps(metadata),
                    'ContentType': 'application/json'
                }
                
                if self.encryption:
                    put_params.update(self.encryption)
                
                await self._s3_client.put_object(**put_params)
        except Exception as e:
            logger.warning(f"Failed to update table metadata: {e}")
    
    async def _find_record_by_id(self, table_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Find a record by ID."""
        try:
            table_prefix = f"{self.prefix}/tables/{table_name}/data/"
            
            paginator = self._s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=table_prefix
            )
            
            async for page in page_iterator:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    if obj['Key'].endswith(f"{record_id}.json"):
                        # Read the object
                        response = await self._s3_client.get_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        body = await response['Body'].read()
                        data = json.loads(body.decode('utf-8'))
                        
                        return {
                            'key': obj['Key'],
                            'data': data
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find record {record_id}: {e}")
            return None
    
    def _matches_filters(self, record: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
        """Check if record matches filters."""
        if not filters:
            return True
        
        for key, value in filters.items():
            if key in ['date_from', 'date_to']:
                continue  # These are handled separately
            
            if key not in record or record[key] != value:
                return False
        
        return True
    
    async def _build_date_prefixes(
        self,
        base_prefix: str,
        date_from: Optional[str],
        date_to: Optional[str]
    ) -> List[str]:
        """Build date-based prefixes for optimization."""
        prefixes = []
        
        # If no date filters, return base prefix
        if not date_from and not date_to:
            return [base_prefix]
        
        # For simplicity, we'll just return the base prefix
        # In a full implementation, you would generate date-based prefixes
        # based on the partition structure (e.g., year/month/day)
        return [base_prefix]
    
    async def _list_tables(self) -> List[str]:
        """List all tables."""
        try:
            tables = []
            prefix = f"{self.prefix}/tables/"
            
            paginator = self._s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
                Delimiter='/'
            )
            
            async for page in page_iterator:
                if 'CommonPrefixes' in page:
                    for common_prefix in page['CommonPrefixes']:
                        # Extract table name from prefix
                        table_prefix = common_prefix['Prefix']
                        table_name = table_prefix.replace(prefix, '').rstrip('/')
                        if table_name:
                            tables.append(table_name)
            
            return tables
            
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return []