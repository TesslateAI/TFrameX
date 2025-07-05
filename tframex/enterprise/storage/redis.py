"""
Redis storage backend for TFrameX Enterprise.

Provides high-performance in-memory storage with persistence options.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis
    from redis.asyncio import ConnectionPool
    from redis.exceptions import RedisError, ConnectionError, TimeoutError
except ImportError:
    raise ImportError(
        "Redis support requires 'redis' package. "
        "Install with: pip install redis[hiredis]"
    )

from .base import BaseStorage

logger = logging.getLogger(__name__)


class RedisStorage(BaseStorage):
    """Redis-based storage implementation for TFrameX Enterprise."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Redis storage with configuration."""
        super().__init__(config)
        
        # Redis configuration
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 6379)
        self.db = config.get("db", 0)
        self.password = config.get("password")
        self.ssl = config.get("ssl", False)
        self.connection_pool_size = config.get("connection_pool_size", 10)
        self.socket_timeout = config.get("socket_timeout", 5)
        self.retry_on_timeout = config.get("retry_on_timeout", True)
        self.health_check_interval = config.get("health_check_interval", 30)
        self.key_prefix = config.get("key_prefix", "tframex:")
        
        # TTL configuration
        self.ttl_config = config.get("ttl", {})
        self.session_ttl = self.ttl_config.get("sessions", 3600)  # 1 hour default
        self.temp_data_ttl = self.ttl_config.get("temp_data", 300)  # 5 minutes default
        
        # Connection pool and client
        self.pool: Optional[ConnectionPool] = None
        self.redis: Optional[redis.Redis] = None
        
        logger.info(f"RedisStorage initialized with host={self.host}:{self.port}, db={self.db}")
    
    async def initialize(self) -> None:
        """Initialize Redis connection pool and client."""
        try:
            # Create connection pool
            pool_kwargs = {
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "password": self.password,
                "max_connections": self.connection_pool_size,
                "socket_timeout": self.socket_timeout,
                "retry_on_timeout": self.retry_on_timeout,
                "health_check_interval": self.health_check_interval,
                "decode_responses": True  # Return strings instead of bytes
            }
            
            # Only add SSL if needed and supported
            if self.ssl:
                # For SSL support, additional configuration might be needed
                # Currently, standard redis-py doesn't directly support ssl parameter
                logger.warning("SSL configuration requested but may require additional setup")
            
            self.pool = ConnectionPool(**pool_kwargs)
            
            # Create Redis client
            self.redis = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.redis.ping()
            
            # Create indexes if needed
            await self._create_indexes()
            
            self._connected = True
            logger.info("RedisStorage initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RedisStorage: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up Redis connections."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Establish connection to Redis - already done in initialize."""
        if not self._connected:
            await self.initialize()
    
    async def disconnect(self) -> None:
        """Close Redis connections."""
        try:
            if self.redis:
                await self.redis.close()
            if self.pool:
                await self.pool.disconnect()
            self._connected = False
            logger.info("RedisStorage disconnected successfully")
        except Exception as e:
            logger.error(f"Error during RedisStorage disconnect: {e}")
    
    async def ping(self) -> bool:
        """Test if Redis is accessible."""
        if not self.redis:
            return False
        try:
            return await self.redis.ping()
        except Exception:
            return False
    
    def _key(self, *parts: str) -> str:
        """Generate a namespaced Redis key."""
        return self.key_prefix + ":".join(parts)
    
    async def _create_indexes(self) -> None:
        """Create any necessary Redis indexes or data structures."""
        # Redis doesn't need explicit index creation like SQL databases
        # But we can set up some utility keys
        await self.redis.set(self._key("meta", "version"), "1.0")
        await self.redis.set(self._key("meta", "created_at"), datetime.now(timezone.utc).isoformat())
    
    # Conversation Management
    
    async def store_conversation(self, conversation_id: str, agent_id: str, 
                                user_id: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a conversation."""
        conversation_key = self._key("conversations", conversation_id)
        
        data = {
            "conversation_id": conversation_id,
            "agent_id": agent_id,
            "user_id": user_id or "anonymous",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": json.dumps(metadata or {})
        }
        
        await self.redis.hset(conversation_key, mapping=data)
        
        # Add to user's conversation set if user_id provided
        if user_id:
            user_conversations_key = self._key("user_conversations", user_id)
            await self.redis.sadd(user_conversations_key, conversation_id)
        
        # Add to agent's conversation set
        agent_conversations_key = self._key("agent_conversations", agent_id)
        await self.redis.sadd(agent_conversations_key, conversation_id)
        
        logger.debug(f"Stored conversation {conversation_id}")
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a conversation."""
        conversation_key = self._key("conversations", conversation_id)
        data = await self.redis.hgetall(conversation_key)
        
        if not data:
            return None
        
        # Parse metadata
        data["metadata"] = json.loads(data.get("metadata", "{}"))
        return data
    
    async def list_conversations(self, user_id: Optional[str] = None,
                                agent_id: Optional[str] = None,
                                limit: int = 100,
                                offset: int = 0) -> List[Dict[str, Any]]:
        """List conversations with optional filtering."""
        conversation_ids = set()
        
        if user_id:
            user_conversations_key = self._key("user_conversations", user_id)
            user_convs = await self.redis.smembers(user_conversations_key)
            conversation_ids.update(user_convs)
        
        if agent_id:
            agent_conversations_key = self._key("agent_conversations", agent_id)
            agent_convs = await self.redis.smembers(agent_conversations_key)
            if conversation_ids:
                conversation_ids = conversation_ids.intersection(agent_convs)
            else:
                conversation_ids = agent_convs
        
        # If no filters, get all conversations (use with caution in production)
        if not user_id and not agent_id:
            pattern = self._key("conversations", "*")
            keys = await self.redis.keys(pattern)
            conversation_ids = {key.split(":")[-1] for key in keys}
        
        # Convert to list and apply pagination
        conversation_ids = list(conversation_ids)
        conversation_ids.sort(reverse=True)  # Most recent first
        paginated_ids = conversation_ids[offset:offset + limit]
        
        # Fetch conversation data
        conversations = []
        for conv_id in paginated_ids:
            conv = await self.get_conversation(conv_id)
            if conv:
                conversations.append(conv)
        
        return conversations
    
    # Message Management
    
    async def store_message(self, conversation_id: str, message: Dict[str, Any]) -> str:
        """Store a message in a conversation."""
        # Generate message ID if not provided
        message_id = message.get("id") or f"{conversation_id}:{datetime.now(timezone.utc).timestamp()}"
        message["id"] = message_id
        message["conversation_id"] = conversation_id
        message["timestamp"] = message.get("timestamp") or datetime.now(timezone.utc).isoformat()
        
        # Store message data
        message_key = self._key("messages", message_id)
        await self.redis.hset(message_key, mapping={
            "data": json.dumps(message),
            "conversation_id": conversation_id,
            "timestamp": message["timestamp"]
        })
        
        # Add to conversation's message list (sorted set for ordering)
        conversation_messages_key = self._key("conversation_messages", conversation_id)
        timestamp_score = datetime.fromisoformat(message["timestamp"]).timestamp()
        await self.redis.zadd(conversation_messages_key, {message_id: timestamp_score})
        
        # Update conversation's updated_at
        conversation_key = self._key("conversations", conversation_id)
        await self.redis.hset(conversation_key, "updated_at", datetime.now(timezone.utc).isoformat())
        
        logger.debug(f"Stored message {message_id} in conversation {conversation_id}")
        return message_id
    
    async def get_messages(self, conversation_id: str, 
                          limit: int = 100,
                          offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve messages from a conversation."""
        conversation_messages_key = self._key("conversation_messages", conversation_id)
        
        # Get message IDs from sorted set (ordered by timestamp)
        message_ids = await self.redis.zrange(
            conversation_messages_key, 
            offset, 
            offset + limit - 1
        )
        
        # Fetch message data
        messages = []
        for msg_id in message_ids:
            message_key = self._key("messages", msg_id)
            msg_data = await self.redis.hget(message_key, "data")
            if msg_data:
                messages.append(json.loads(msg_data))
        
        return messages
    
    # Flow Management
    
    async def store_flow_execution(self, flow_id: str, flow_name: str,
                                  status: str, result: Optional[Any] = None,
                                  error: Optional[str] = None,
                                  metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store flow execution details."""
        flow_key = self._key("flows", flow_id)
        
        data = {
            "flow_id": flow_id,
            "flow_name": flow_name,
            "status": status,
            "result": json.dumps(result) if result else None,
            "error": error,
            "metadata": json.dumps(metadata or {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.redis.hset(flow_key, mapping=data)
        
        # Add to flow name index
        flow_name_key = self._key("flow_executions", flow_name)
        await self.redis.sadd(flow_name_key, flow_id)
        
        logger.debug(f"Stored flow execution {flow_id}")
    
    async def get_flow_execution(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve flow execution details."""
        flow_key = self._key("flows", flow_id)
        data = await self.redis.hgetall(flow_key)
        
        if not data:
            return None
        
        # Parse JSON fields
        if data.get("result"):
            data["result"] = json.loads(data["result"])
        data["metadata"] = json.loads(data.get("metadata", "{}"))
        
        return data
    
    # Audit Logging
    
    async def store_audit_log(self, event_type: str, user_id: Optional[str],
                             resource_type: str, resource_id: str,
                             action: str, details: Optional[Dict[str, Any]] = None,
                             ip_address: Optional[str] = None,
                             user_agent: Optional[str] = None) -> None:
        """Store an audit log entry."""
        timestamp = datetime.now(timezone.utc)
        audit_id = f"{event_type}:{resource_type}:{resource_id}:{timestamp.timestamp()}"
        
        audit_data = {
            "audit_id": audit_id,
            "event_type": event_type,
            "user_id": user_id or "system",
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "details": json.dumps(details or {}),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": timestamp.isoformat()
        }
        
        # Store audit entry
        audit_key = self._key("audit", audit_id)
        await self.redis.hset(audit_key, mapping=audit_data)
        
        # Add to daily audit log (sorted set)
        daily_key = self._key("audit_daily", timestamp.strftime("%Y-%m-%d"))
        await self.redis.zadd(daily_key, {audit_id: timestamp.timestamp()})
        
        # Set TTL on daily audit logs if configured
        if hasattr(self, 'audit_retention_days'):
            ttl_seconds = self.audit_retention_days * 86400
            await self.redis.expire(daily_key, ttl_seconds)
        
        logger.debug(f"Stored audit log {audit_id}")
    
    async def get_audit_logs(self, start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            user_id: Optional[str] = None,
                            resource_type: Optional[str] = None,
                            event_type: Optional[str] = None,
                            limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering."""
        # Default date range if not specified
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        audit_entries = []
        current_date = start_date
        
        # Iterate through daily audit logs
        while current_date <= end_date and len(audit_entries) < limit:
            daily_key = self._key("audit_daily", current_date.strftime("%Y-%m-%d"))
            
            # Get audit IDs for the day
            audit_ids = await self.redis.zrange(daily_key, 0, -1)
            
            for audit_id in audit_ids:
                if len(audit_entries) >= limit:
                    break
                
                audit_key = self._key("audit", audit_id)
                audit_data = await self.redis.hgetall(audit_key)
                
                if not audit_data:
                    continue
                
                # Apply filters
                if user_id and audit_data.get("user_id") != user_id:
                    continue
                if resource_type and audit_data.get("resource_type") != resource_type:
                    continue
                if event_type and audit_data.get("event_type") != event_type:
                    continue
                
                # Parse JSON fields
                audit_data["details"] = json.loads(audit_data.get("details", "{}"))
                audit_entries.append(audit_data)
            
            # Move to next day
            current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
            current_date = current_date.replace(day=current_date.day + 1)
        
        return audit_entries
    
    # User and Role Management
    
    async def store_user(self, user_id: str, username: str, email: str,
                        role_ids: List[str], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store user information."""
        user_key = self._key("users", user_id)
        
        data = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "role_ids": json.dumps(role_ids),
            "metadata": json.dumps(metadata or {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.redis.hset(user_key, mapping=data)
        
        # Add to username index
        username_key = self._key("username_index", username.lower())
        await self.redis.set(username_key, user_id)
        
        # Add to email index
        email_key = self._key("email_index", email.lower())
        await self.redis.set(email_key, user_id)
        
        logger.debug(f"Stored user {user_id}")
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user information."""
        user_key = self._key("users", user_id)
        data = await self.redis.hgetall(user_key)
        
        if not data:
            return None
        
        # Parse JSON fields
        data["role_ids"] = json.loads(data.get("role_ids", "[]"))
        data["metadata"] = json.loads(data.get("metadata", "{}"))
        
        return data
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by username."""
        username_key = self._key("username_index", username.lower())
        user_id = await self.redis.get(username_key)
        
        if not user_id:
            return None
        
        return await self.get_user(user_id)
    
    async def store_role(self, role_id: str, role_name: str,
                        permissions: List[str], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store role information."""
        role_key = self._key("roles", role_id)
        
        data = {
            "role_id": role_id,
            "role_name": role_name,
            "permissions": json.dumps(permissions),
            "metadata": json.dumps(metadata or {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.redis.hset(role_key, mapping=data)
        
        # Add to role name index
        role_name_key = self._key("role_name_index", role_name.lower())
        await self.redis.set(role_name_key, role_id)
        
        logger.debug(f"Stored role {role_id}")
    
    async def get_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve role information."""
        role_key = self._key("roles", role_id)
        data = await self.redis.hgetall(role_key)
        
        if not data:
            return None
        
        # Parse JSON fields
        data["permissions"] = json.loads(data.get("permissions", "[]"))
        data["metadata"] = json.loads(data.get("metadata", "{}"))
        
        return data
    
    # Session Management
    
    async def store_session(self, session_id: str, user_id: str,
                           data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Store session data with optional TTL."""
        session_key = self._key("sessions", session_id)
        ttl = ttl or self.session_ttl
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "data": json.dumps(data),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": datetime.now(timezone.utc).timestamp() + ttl
        }
        
        await self.redis.hset(session_key, mapping=session_data)
        await self.redis.expire(session_key, ttl)
        
        # Add to user's session set
        user_sessions_key = self._key("user_sessions", user_id)
        await self.redis.sadd(user_sessions_key, session_id)
        await self.redis.expire(user_sessions_key, ttl)
        
        logger.debug(f"Stored session {session_id} with TTL {ttl}s")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        session_key = self._key("sessions", session_id)
        data = await self.redis.hgetall(session_key)
        
        if not data:
            return None
        
        # Check if session expired
        expires_at = float(data.get("expires_at", 0))
        if expires_at < datetime.now(timezone.utc).timestamp():
            await self.delete_session(session_id)
            return None
        
        # Parse session data
        data["data"] = json.loads(data.get("data", "{}"))
        
        return data
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        session_key = self._key("sessions", session_id)
        
        # Get user_id before deletion
        session_data = await self.redis.hget(session_key, "user_id")
        
        # Delete session
        await self.redis.delete(session_key)
        
        # Remove from user's session set
        if session_data:
            user_sessions_key = self._key("user_sessions", session_data)
            await self.redis.srem(user_sessions_key, session_id)
        
        logger.debug(f"Deleted session {session_id}")
    
    # Health and Statistics
    
    async def health_check(self) -> Tuple[bool, Dict[str, Any]]:
        """Check Redis health and return statistics."""
        try:
            # Ping Redis
            await self.redis.ping()
            
            # Get Redis info
            info = await self.redis.info()
            
            # Get key statistics
            pattern = self._key("*")
            total_keys = len(await self.redis.keys(pattern))
            
            stats = {
                "status": "healthy",
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_keys": total_keys,
                "uptime_in_seconds": info.get("uptime_in_seconds"),
                "role": info.get("role")
            }
            
            return True, stats
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False, {"status": "unhealthy", "error": str(e)}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            # Count different types of data
            conv_pattern = self._key("conversations", "*")
            msg_pattern = self._key("messages", "*")
            flow_pattern = self._key("flows", "*")
            user_pattern = self._key("users", "*")
            role_pattern = self._key("roles", "*")
            session_pattern = self._key("sessions", "*")
            
            stats = {
                "conversations": len(await self.redis.keys(conv_pattern)),
                "messages": len(await self.redis.keys(msg_pattern)),
                "flows": len(await self.redis.keys(flow_pattern)),
                "users": len(await self.redis.keys(user_pattern)),
                "roles": len(await self.redis.keys(role_pattern)),
                "active_sessions": len(await self.redis.keys(session_pattern))
            }
            
            # Add Redis-specific stats
            info = await self.redis.info()
            stats.update({
                "memory_usage": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed"),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec")
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    # Backup and Migration
    
    async def export_data(self, output_path: str) -> None:
        """Export all data to a JSON file."""
        export_data = {
            "conversations": [],
            "messages": [],
            "flows": [],
            "users": [],
            "roles": [],
            "audit_logs": []
        }
        
        # Export conversations
        conv_pattern = self._key("conversations", "*")
        for key in await self.redis.keys(conv_pattern):
            conv_id = key.split(":")[-1]
            conv = await self.get_conversation(conv_id)
            if conv:
                export_data["conversations"].append(conv)
        
        # Export messages
        msg_pattern = self._key("messages", "*")
        for key in await self.redis.keys(msg_pattern):
            msg_data = await self.redis.hget(key, "data")
            if msg_data:
                export_data["messages"].append(json.loads(msg_data))
        
        # Export flows
        flow_pattern = self._key("flows", "*")
        for key in await self.redis.keys(flow_pattern):
            flow_id = key.split(":")[-1]
            flow = await self.get_flow_execution(flow_id)
            if flow:
                export_data["flows"].append(flow)
        
        # Export users
        user_pattern = self._key("users", "*")
        for key in await self.redis.keys(user_pattern):
            user_id = key.split(":")[-1]
            user = await self.get_user(user_id)
            if user:
                export_data["users"].append(user)
        
        # Export roles
        role_pattern = self._key("roles", "*")
        for key in await self.redis.keys(role_pattern):
            role_id = key.split(":")[-1]
            role = await self.get_role(role_id)
            if role:
                export_data["roles"].append(role)
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported data to {output_path}")
    
    async def import_data(self, input_path: str) -> None:
        """Import data from a JSON file."""
        with open(input_path, 'r') as f:
            import_data = json.load(f)
        
        # Import roles first (users depend on them)
        for role in import_data.get("roles", []):
            await self.store_role(
                role["role_id"],
                role["role_name"],
                role["permissions"],
                role.get("metadata", {})
            )
        
        # Import users
        for user in import_data.get("users", []):
            await self.store_user(
                user["user_id"],
                user["username"],
                user["email"],
                user["role_ids"],
                user.get("metadata", {})
            )
        
        # Import conversations
        for conv in import_data.get("conversations", []):
            await self.store_conversation(
                conv["conversation_id"],
                conv["agent_id"],
                conv.get("user_id"),
                conv.get("metadata", {})
            )
        
        # Import messages
        for msg in import_data.get("messages", []):
            await self.store_message(msg["conversation_id"], msg)
        
        # Import flows
        for flow in import_data.get("flows", []):
            await self.store_flow_execution(
                flow["flow_id"],
                flow["flow_name"],
                flow["status"],
                flow.get("result"),
                flow.get("error"),
                flow.get("metadata", {})
            )
        
        logger.info(f"Imported data from {input_path}")
    
    # Abstract methods implementation for BaseStorage compatibility
    
    async def create_table(self, table_name: str, schema: Dict[str, Any]) -> None:
        """Create a table - no-op for Redis as it's schema-less."""
        # Redis doesn't need table creation
        logger.debug(f"create_table called for {table_name} - no-op for Redis")
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> str:
        """Insert a record - delegates to appropriate method based on table."""
        record_id = data.get("id") or str(datetime.now(timezone.utc).timestamp())
        
        if table_name == "conversations":
            await self.store_conversation(
                data.get("conversation_id", record_id),
                data.get("agent_id", ""),
                data.get("user_id"),
                data.get("metadata", {})
            )
        elif table_name == "messages":
            await self.store_message(data.get("conversation_id", ""), data)
        elif table_name == "users":
            await self.store_user(
                data.get("user_id", record_id),
                data.get("username", ""),
                data.get("email", ""),
                data.get("role_ids", []),
                data.get("metadata", {})
            )
        elif table_name == "roles":
            await self.store_role(
                data.get("role_id", record_id),
                data.get("role_name", ""),
                data.get("permissions", []),
                data.get("metadata", {})
            )
        else:
            # Generic storage
            key = self._key(table_name, record_id)
            await self.redis.hset(key, mapping={"data": json.dumps(data)})
        
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
        """Select records - delegates based on table."""
        if table_name == "conversations":
            convs = await self.list_conversations(
                user_id=filters.get("user_id") if filters else None,
                agent_id=filters.get("agent_id") if filters else None,
                limit=limit or 100,
                offset=offset or 0
            )
            return convs
        elif table_name == "audit_logs":
            logs = await self.get_audit_logs(
                user_id=filters.get("user_id") if filters else None,
                event_type=filters.get("event_type") if filters else None,
                limit=limit or 1000
            )
            return logs
        else:
            # Generic select - scan keys
            pattern = self._key(table_name, "*")
            keys = await self.redis.keys(pattern)
            results = []
            
            for key in keys:
                data_str = await self.redis.hget(key, "data")
                if data_str:
                    data = json.loads(data_str)
                    
                    # Apply filters
                    if filters:
                        match = all(data.get(k) == v for k, v in filters.items())
                        if not match:
                            continue
                    
                    results.append(data)
            
            # Apply limit and offset
            if offset:
                results = results[offset:]
            if limit:
                results = results[:limit]
            
            return results
    
    async def update(self, table_name: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Update a record."""
        key = self._key(table_name, record_id)
        exists = await self.redis.exists(key)
        
        if not exists:
            return False
        
        # Get existing data
        existing_str = await self.redis.hget(key, "data")
        if existing_str:
            existing = json.loads(existing_str)
            existing.update(data)
            await self.redis.hset(key, "data", json.dumps(existing))
        
        return True
    
    async def delete(self, table_name: str, record_id: str) -> bool:
        """Delete a record."""
        key = self._key(table_name, record_id)
        result = await self.redis.delete(key)
        return result > 0
    
    async def count(self, table_name: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records in a table."""
        pattern = self._key(table_name, "*")
        keys = await self.redis.keys(pattern)
        
        if not filters:
            return len(keys)
        
        # Count with filters
        count = 0
        for key in keys:
            data_str = await self.redis.hget(key, "data")
            if data_str:
                data = json.loads(data_str)
                match = all(data.get(k) == v for k, v in filters.items())
                if match:
                    count += 1
        
        return count
    
    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute raw Redis command."""
        # Parse the query as a Redis command
        parts = query.split()
        if not parts:
            raise ValueError("Empty query")
        
        command = parts[0].upper()
        args = parts[1:]
        
        # Execute Redis command
        try:
            return await self.redis.execute_command(command, *args)
        except Exception as e:
            logger.error(f"Failed to execute raw Redis command: {e}")
            raise