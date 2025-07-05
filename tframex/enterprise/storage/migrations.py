"""
Migration Management System

This module provides database migration capabilities for creating and updating
database schemas across different storage backends.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .base import BaseStorage

logger = logging.getLogger(__name__)


class Migration(ABC):
    """
    Abstract base class for database migrations.
    """
    
    def __init__(self, version: str, description: str):
        """
        Initialize migration.
        
        Args:
            version: Migration version (e.g., "001", "1.0.0")
            description: Human-readable description of the migration
        """
        self.version = version
        self.description = description
        self.applied_at: Optional[datetime] = None
    
    @abstractmethod
    async def up(self, storage: BaseStorage) -> None:
        """
        Apply the migration.
        
        Args:
            storage: Storage backend to apply migration to
        """
        pass
    
    @abstractmethod
    async def down(self, storage: BaseStorage) -> None:
        """
        Rollback the migration.
        
        Args:
            storage: Storage backend to rollback migration from
        """
        pass
    
    def __str__(self) -> str:
        return f"Migration {self.version}: {self.description}"


class CreateTablesV001(Migration):
    """
    Initial migration to create all enterprise tables.
    """
    
    def __init__(self):
        super().__init__("001", "Create initial enterprise tables")
    
    async def up(self, storage: BaseStorage) -> None:
        """Create all enterprise tables."""
        logger.info("Creating enterprise tables...")
        
        # Users table
        await storage.create_table("users", {
            "id": "UUID PRIMARY KEY",
            "username": "VARCHAR(255) UNIQUE NOT NULL",
            "email": "VARCHAR(255) UNIQUE",
            "password_hash": "VARCHAR(255)",
            "is_active": "BOOLEAN DEFAULT TRUE",
            "created_at": "TIMESTAMP DEFAULT NOW()",
            "updated_at": "TIMESTAMP",
            "metadata": "JSONB"
        })
        
        # Roles table
        await storage.create_table("roles", {
            "id": "UUID PRIMARY KEY",
            "name": "VARCHAR(100) UNIQUE NOT NULL",
            "description": "TEXT",
            "created_at": "TIMESTAMP DEFAULT NOW()"
        })
        
        # Permissions table
        await storage.create_table("permissions", {
            "id": "UUID PRIMARY KEY",
            "name": "VARCHAR(100) UNIQUE NOT NULL",
            "resource": "VARCHAR(100) NOT NULL",
            "action": "VARCHAR(50) NOT NULL",
            "description": "TEXT"
        })
        
        # Role permissions junction table
        await storage.create_table("role_permissions", {
            "role_id": "UUID REFERENCES roles(id)",
            "permission_id": "UUID REFERENCES permissions(id)",
            "PRIMARY KEY": "(role_id, permission_id)"
        })
        
        # User roles junction table
        await storage.create_table("user_roles", {
            "user_id": "UUID REFERENCES users(id)",
            "role_id": "UUID REFERENCES roles(id)",
            "assigned_at": "TIMESTAMP DEFAULT NOW()",
            "assigned_by": "UUID REFERENCES users(id)",
            "PRIMARY KEY": "(user_id, role_id)"
        })
        
        # Conversations table
        await storage.create_table("conversations", {
            "id": "UUID PRIMARY KEY",
            "user_id": "UUID REFERENCES users(id)",
            "agent_name": "VARCHAR(255) NOT NULL",
            "title": "VARCHAR(500)",
            "created_at": "TIMESTAMP DEFAULT NOW()",
            "updated_at": "TIMESTAMP",
            "metadata": "JSONB"
        })
        
        # Messages table
        await storage.create_table("messages", {
            "id": "UUID PRIMARY KEY",
            "conversation_id": "UUID REFERENCES conversations(id)",
            "role": "VARCHAR(20) NOT NULL",
            "content": "TEXT",
            "tool_calls": "JSONB",
            "tool_call_id": "VARCHAR(255)",
            "name": "VARCHAR(255)",
            "created_at": "TIMESTAMP DEFAULT NOW()",
            "metadata": "JSONB"
        })
        
        # Flow executions table
        await storage.create_table("flow_executions", {
            "id": "UUID PRIMARY KEY",
            "user_id": "UUID REFERENCES users(id)",
            "flow_name": "VARCHAR(255) NOT NULL",
            "status": "VARCHAR(50) DEFAULT 'running'",
            "initial_input": "TEXT",
            "final_output": "TEXT",
            "started_at": "TIMESTAMP DEFAULT NOW()",
            "completed_at": "TIMESTAMP",
            "error_message": "TEXT",
            "metadata": "JSONB"
        })
        
        # Flow steps table
        await storage.create_table("flow_steps", {
            "id": "UUID PRIMARY KEY",
            "execution_id": "UUID REFERENCES flow_executions(id)",
            "step_name": "VARCHAR(255) NOT NULL",
            "step_type": "VARCHAR(100) NOT NULL",
            "input_data": "TEXT",
            "output_data": "TEXT",
            "status": "VARCHAR(50) DEFAULT 'pending'",
            "started_at": "TIMESTAMP",
            "completed_at": "TIMESTAMP",
            "error_message": "TEXT",
            "step_order": "INTEGER NOT NULL"
        })
        
        # Agent executions table
        await storage.create_table("agent_executions", {
            "id": "UUID PRIMARY KEY",
            "user_id": "UUID REFERENCES users(id)",
            "conversation_id": "UUID REFERENCES conversations(id)",
            "flow_execution_id": "UUID REFERENCES flow_executions(id)",
            "agent_name": "VARCHAR(255) NOT NULL",
            "input_message": "TEXT",
            "output_message": "TEXT",
            "execution_time_ms": "INTEGER",
            "tool_calls_count": "INTEGER DEFAULT 0",
            "status": "VARCHAR(50) DEFAULT 'success'",
            "error_message": "TEXT",
            "started_at": "TIMESTAMP DEFAULT NOW()",
            "completed_at": "TIMESTAMP",
            "metadata": "JSONB"
        })
        
        # Tool calls table
        await storage.create_table("tool_calls", {
            "id": "UUID PRIMARY KEY",
            "agent_execution_id": "UUID REFERENCES agent_executions(id)",
            "tool_name": "VARCHAR(255) NOT NULL",
            "tool_type": "VARCHAR(50) NOT NULL",
            "arguments": "JSONB",
            "result": "TEXT",
            "execution_time_ms": "INTEGER",
            "status": "VARCHAR(50) DEFAULT 'success'",
            "error_message": "TEXT",
            "called_at": "TIMESTAMP DEFAULT NOW()",
            "completed_at": "TIMESTAMP"
        })
        
        # Metrics table
        await storage.create_table("metrics", {
            "id": "UUID PRIMARY KEY",
            "metric_name": "VARCHAR(255) NOT NULL",
            "metric_type": "VARCHAR(50) NOT NULL",
            "value": "DECIMAL",
            "labels": "JSONB",
            "timestamp": "TIMESTAMP DEFAULT NOW()",
            "source": "VARCHAR(100)"
        })
        
        # Events table
        await storage.create_table("events", {
            "id": "UUID PRIMARY KEY",
            "event_type": "VARCHAR(100) NOT NULL",
            "event_source": "VARCHAR(100) NOT NULL",
            "user_id": "UUID REFERENCES users(id)",
            "resource_type": "VARCHAR(100)",
            "resource_id": "VARCHAR(255)",
            "action": "VARCHAR(100) NOT NULL",
            "status": "VARCHAR(50) DEFAULT 'success'",
            "details": "JSONB",
            "ip_address": "INET",
            "user_agent": "TEXT",
            "created_at": "TIMESTAMP DEFAULT NOW()"
        })
        
        # Audit logs table
        await storage.create_table("audit_logs", {
            "id": "UUID PRIMARY KEY",
            "user_id": "UUID REFERENCES users(id)",
            "action": "VARCHAR(100) NOT NULL",
            "resource_type": "VARCHAR(100) NOT NULL",
            "resource_id": "VARCHAR(255)",
            "old_values": "JSONB",
            "new_values": "JSONB",
            "ip_address": "INET",
            "user_agent": "TEXT",
            "created_at": "TIMESTAMP DEFAULT NOW()"
        })
        
        logger.info("Enterprise tables created successfully")
    
    async def down(self, storage: BaseStorage) -> None:
        """Drop all enterprise tables."""
        logger.info("Dropping enterprise tables...")
        
        tables = [
            "audit_logs",
            "events", 
            "metrics",
            "tool_calls",
            "agent_executions",
            "flow_steps",
            "flow_executions",
            "messages",
            "conversations",
            "user_roles",
            "role_permissions",
            "permissions",
            "roles",
            "users"
        ]
        
        for table in tables:
            try:
                await storage.execute_raw(f"DROP TABLE IF EXISTS {table} CASCADE")
            except Exception as e:
                logger.warning(f"Failed to drop table {table}: {e}")
        
        logger.info("Enterprise tables dropped")


class SeedDefaultDataV002(Migration):
    """
    Migration to seed default roles and permissions.
    """
    
    def __init__(self):
        super().__init__("002", "Seed default roles and permissions")
    
    async def up(self, storage: BaseStorage) -> None:
        """Seed default data."""
        logger.info("Seeding default roles and permissions...")
        
        # Default permissions
        permissions = [
            {"name": "agent.execute", "resource": "agent", "action": "execute", "description": "Execute agents"},
            {"name": "agent.view", "resource": "agent", "action": "view", "description": "View agent definitions"},
            {"name": "agent.manage", "resource": "agent", "action": "manage", "description": "Create/modify agents"},
            {"name": "tool.call", "resource": "tool", "action": "call", "description": "Call tools"},
            {"name": "tool.view", "resource": "tool", "action": "view", "description": "View tool definitions"},
            {"name": "tool.manage", "resource": "tool", "action": "manage", "description": "Create/modify tools"},
            {"name": "flow.execute", "resource": "flow", "action": "execute", "description": "Execute flows"},
            {"name": "flow.view", "resource": "flow", "action": "view", "description": "View flow definitions"},
            {"name": "flow.manage", "resource": "flow", "action": "manage", "description": "Create/modify flows"},
            {"name": "data.read", "resource": "data", "action": "read", "description": "Read conversation data"},
            {"name": "data.write", "resource": "data", "action": "write", "description": "Write conversation data"},
            {"name": "data.delete", "resource": "data", "action": "delete", "description": "Delete data"},
            {"name": "user.manage", "resource": "user", "action": "manage", "description": "Manage users"},
            {"name": "role.manage", "resource": "role", "action": "manage", "description": "Manage roles"},
            {"name": "system.admin", "resource": "system", "action": "admin", "description": "System administration"},
            {"name": "metrics.view", "resource": "metrics", "action": "view", "description": "View metrics"},
            {"name": "audit.view", "resource": "audit", "action": "view", "description": "View audit logs"}
        ]
        
        for perm in permissions:
            perm["id"] = str(uuid4())
            await storage.save_model(type('Permission', (), perm)(), "permissions")
        
        # Default roles
        roles = [
            {
                "id": str(uuid4()),
                "name": "user",
                "description": "Standard user with basic permissions",
                "permissions": ["agent.execute", "tool.call", "flow.execute", "data.read", "data.write"]
            },
            {
                "id": str(uuid4()),
                "name": "developer", 
                "description": "Developer with read access to definitions",
                "permissions": ["agent.view", "tool.view", "flow.view", "metrics.view"]
            },
            {
                "id": str(uuid4()),
                "name": "admin",
                "description": "Administrator with full access",
                "permissions": ["user.manage", "role.manage", "system.admin", "audit.view"]
            },
            {
                "id": str(uuid4()),
                "name": "operator",
                "description": "Operations team with monitoring access", 
                "permissions": ["metrics.view", "system.admin"]
            }
        ]
        
        for role in roles:
            await storage.save_model(type('Role', (), role)(), "roles")
        
        logger.info("Default roles and permissions seeded")
    
    async def down(self, storage: BaseStorage) -> None:
        """Remove default data."""
        logger.info("Removing default roles and permissions...")
        
        # Remove default roles
        default_roles = ["user", "developer", "admin", "operator"]
        for role_name in default_roles:
            try:
                roles = await storage.select("roles", {"name": role_name})
                for role in roles:
                    await storage.delete("roles", role["id"])
            except Exception as e:
                logger.warning(f"Failed to remove role {role_name}: {e}")
        
        # Remove default permissions 
        default_permissions = [
            "agent.execute", "agent.view", "agent.manage",
            "tool.call", "tool.view", "tool.manage",
            "flow.execute", "flow.view", "flow.manage",
            "data.read", "data.write", "data.delete",
            "user.manage", "role.manage", "system.admin",
            "metrics.view", "audit.view"
        ]
        
        for perm_name in default_permissions:
            try:
                permissions = await storage.select("permissions", {"name": perm_name})
                for perm in permissions:
                    await storage.delete("permissions", perm["id"])
            except Exception as e:
                logger.warning(f"Failed to remove permission {perm_name}: {e}")
        
        logger.info("Default roles and permissions removed")


class MigrationManager:
    """
    Manages database migrations across different storage backends.
    """
    
    def __init__(self, storage: BaseStorage):
        """
        Initialize migration manager.
        
        Args:
            storage: Storage backend to manage migrations for
        """
        self.storage = storage
        self.migrations: List[Migration] = []
        self._migration_table = "schema_migrations"
        
        # Register built-in migrations
        self.register_migration(CreateTablesV001())
        self.register_migration(SeedDefaultDataV002())
    
    def register_migration(self, migration: Migration) -> None:
        """
        Register a migration.
        
        Args:
            migration: Migration to register
        """
        self.migrations.append(migration)
        self.migrations.sort(key=lambda m: m.version)
    
    async def initialize(self) -> None:
        """
        Initialize the migration system by creating the migrations table.
        """
        try:
            await self.storage.create_table(self._migration_table, {
                "version": "VARCHAR(50) PRIMARY KEY",
                "description": "TEXT NOT NULL",
                "applied_at": "TIMESTAMP DEFAULT NOW()",
                "checksum": "VARCHAR(64)"
            })
            logger.info("Migration system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize migration system: {e}")
            raise
    
    async def get_applied_migrations(self) -> List[str]:
        """
        Get list of applied migration versions.
        
        Returns:
            List of applied migration versions
        """
        try:
            records = await self.storage.select(
                self._migration_table,
                order_by="applied_at",
                order_desc=False
            )
            return [record["version"] for record in records]
        except Exception as e:
            logger.warning(f"Failed to get applied migrations: {e}")
            return []
    
    async def is_migration_applied(self, version: str) -> bool:
        """
        Check if a migration has been applied.
        
        Args:
            version: Migration version to check
            
        Returns:
            True if migration is applied, False otherwise
        """
        applied = await self.get_applied_migrations()
        return version in applied
    
    async def apply_migration(self, migration: Migration) -> None:
        """
        Apply a single migration.
        
        Args:
            migration: Migration to apply
        """
        if await self.is_migration_applied(migration.version):
            logger.info(f"Migration {migration.version} already applied, skipping")
            return
        
        logger.info(f"Applying migration {migration.version}: {migration.description}")
        
        try:
            # Begin transaction if supported
            try:
                await self.storage.begin_transaction()
                transaction_started = True
            except Exception:
                transaction_started = False
                logger.warning("Transaction not supported, applying migration without transaction")
            
            # Apply the migration
            await migration.up(self.storage)
            
            # Record the migration
            migration_record = {
                "version": migration.version,
                "description": migration.description,
                "applied_at": datetime.utcnow().isoformat(),
                "checksum": ""  # Could add checksum validation in the future
            }
            
            await self.storage.insert(self._migration_table, migration_record)
            
            # Commit transaction if supported
            if transaction_started:
                await self.storage.commit_transaction()
            
            migration.applied_at = datetime.utcnow()
            logger.info(f"Migration {migration.version} applied successfully")
            
        except Exception as e:
            # Rollback transaction if supported
            if transaction_started:
                try:
                    await self.storage.rollback_transaction()
                except Exception:
                    pass
            
            logger.error(f"Failed to apply migration {migration.version}: {e}")
            raise
    
    async def rollback_migration(self, migration: Migration) -> None:
        """
        Rollback a single migration.
        
        Args:
            migration: Migration to rollback
        """
        if not await self.is_migration_applied(migration.version):
            logger.info(f"Migration {migration.version} not applied, skipping rollback")
            return
        
        logger.info(f"Rolling back migration {migration.version}: {migration.description}")
        
        try:
            # Begin transaction if supported
            try:
                await self.storage.begin_transaction()
                transaction_started = True
            except Exception:
                transaction_started = False
                logger.warning("Transaction not supported, rolling back migration without transaction")
            
            # Rollback the migration
            await migration.down(self.storage)
            
            # Remove migration record
            records = await self.storage.select(
                self._migration_table,
                {"version": migration.version}
            )
            
            if records:
                await self.storage.delete(self._migration_table, records[0]["id"])
            
            # Commit transaction if supported
            if transaction_started:
                await self.storage.commit_transaction()
            
            migration.applied_at = None
            logger.info(f"Migration {migration.version} rolled back successfully")
            
        except Exception as e:
            # Rollback transaction if supported
            if transaction_started:
                try:
                    await self.storage.rollback_transaction()
                except Exception:
                    pass
            
            logger.error(f"Failed to rollback migration {migration.version}: {e}")
            raise
    
    async def migrate_up(self, target_version: Optional[str] = None) -> None:
        """
        Apply all pending migrations up to target version.
        
        Args:
            target_version: Stop at this version (None for all migrations)
        """
        logger.info("Running database migrations...")
        
        # Ensure migration system is initialized
        await self.initialize()
        
        applied_migrations = await self.get_applied_migrations()
        
        for migration in self.migrations:
            if migration.version in applied_migrations:
                continue
            
            if target_version and migration.version > target_version:
                break
            
            await self.apply_migration(migration)
        
        logger.info("Database migrations completed")
    
    async def migrate_down(self, target_version: str) -> None:
        """
        Rollback migrations down to target version.
        
        Args:
            target_version: Rollback to this version
        """
        logger.info(f"Rolling back migrations to version {target_version}...")
        
        applied_migrations = await self.get_applied_migrations()
        
        # Rollback migrations in reverse order
        for migration in reversed(self.migrations):
            if migration.version not in applied_migrations:
                continue
            
            if migration.version <= target_version:
                break
            
            await self.rollback_migration(migration)
        
        logger.info(f"Rollback to version {target_version} completed")
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """
        Get current migration status.
        
        Returns:
            Migration status information
        """
        try:
            applied_migrations = await self.get_applied_migrations()
            
            status = {
                "total_migrations": len(self.migrations),
                "applied_migrations": len(applied_migrations),
                "pending_migrations": len(self.migrations) - len(applied_migrations),
                "migrations": []
            }
            
            for migration in self.migrations:
                migration_info = {
                    "version": migration.version,
                    "description": migration.description,
                    "applied": migration.version in applied_migrations,
                    "applied_at": migration.applied_at.isoformat() if migration.applied_at else None
                }
                status["migrations"].append(migration_info)
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {
                "error": str(e),
                "total_migrations": len(self.migrations),
                "applied_migrations": 0,
                "pending_migrations": len(self.migrations),
                "migrations": []
            }