# tframex/mcp/roots.py
"""
MCP Roots implementation for TFrameX.
Provides filesystem boundary management with security validation.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass
import asyncio
from urllib.parse import urlparse

logger = logging.getLogger("tframex.mcp.roots")

@dataclass
class Root:
    """Represents a filesystem root boundary."""
    uri: str  # file:// URI
    name: Optional[str] = None  # Human-readable name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP-compatible dictionary."""
        result = {"uri": self.uri}
        if self.name:
            result["name"] = self.name
        return result
    
    @property
    def path(self) -> Path:
        """Get the filesystem path from the URI."""
        parsed = urlparse(self.uri)
        if parsed.scheme != "file":
            raise ValueError(f"Invalid root URI scheme: {parsed.scheme}")
        # Handle both Unix and Windows paths
        if parsed.netloc:  # Windows: file://c:/path
            return Path(f"{parsed.netloc}{parsed.path}")
        return Path(parsed.path)  # Unix: file:///path


class RootsManager:
    """
    Manages filesystem roots for MCP with security validation.
    Implements the client-side roots capability.
    """
    
    def __init__(self, allowed_paths: Optional[List[str]] = None, 
                 require_consent: bool = True):
        """
        Initialize the roots manager.
        
        Args:
            allowed_paths: List of allowed base paths (defaults to safe paths)
            require_consent: Whether to require user consent for roots
        """
        self._roots: List[Root] = []
        self._allowed_base_paths: Set[Path] = set()
        self._require_consent = require_consent
        self._consent_cache: Dict[str, bool] = {}
        self._listeners: List[callable] = []
        self._lock = asyncio.Lock()
        
        # Initialize with default safe paths if none provided
        if allowed_paths is None:
            allowed_paths = [
                os.path.expanduser("~/Documents"),
                os.path.expanduser("~/Desktop"),
                "/tmp",
                os.path.expanduser("~/.tframex/workspaces")
            ]
        
        # Normalize and validate allowed paths
        for path_str in allowed_paths:
            try:
                path = Path(path_str).resolve()
                if path.exists():
                    self._allowed_base_paths.add(path)
                    logger.debug(f"Added allowed base path: {path}")
            except Exception as e:
                logger.warning(f"Invalid allowed path '{path_str}': {e}")
    
    def add_listener(self, callback: callable):
        """Add a listener for roots changes."""
        self._listeners.append(callback)
    
    async def _notify_listeners(self):
        """Notify all listeners of roots changes."""
        for listener in self._listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener()
                else:
                    listener()
            except Exception as e:
                logger.error(f"Error notifying roots listener: {e}")
    
    def _validate_path_security(self, path: Path) -> bool:
        """
        Validate that a path is secure and allowed.
        
        Returns:
            True if path is valid and secure
        """
        try:
            # Resolve to absolute path and check for traversal
            resolved = path.resolve()
            
            # Check if path is within allowed base paths
            for allowed in self._allowed_base_paths:
                try:
                    resolved.relative_to(allowed)
                    return True
                except ValueError:
                    continue
            
            logger.warning(f"Path '{resolved}' not within allowed base paths")
            return False
            
        except Exception as e:
            logger.error(f"Path validation error for '{path}': {e}")
            return False
    
    def _path_to_uri(self, path: Path) -> str:
        """Convert a filesystem path to a file:// URI."""
        # Ensure absolute path
        abs_path = path.resolve()
        
        # Handle Windows vs Unix paths
        if os.name == 'nt':  # Windows
            # Convert C:\path to file:///C:/path
            uri = abs_path.as_uri()
        else:  # Unix-like
            uri = abs_path.as_uri()
        
        return uri
    
    async def add_root(self, path: str, name: Optional[str] = None) -> bool:
        """
        Add a filesystem root with security validation.
        
        Args:
            path: Filesystem path to add as root
            name: Optional human-readable name
            
        Returns:
            True if root was added successfully
        """
        async with self._lock:
            try:
                root_path = Path(path).resolve()
                
                # Security validation
                if not self._validate_path_security(root_path):
                    logger.error(f"Security validation failed for root: {path}")
                    return False
                
                # Check if path exists
                if not root_path.exists():
                    logger.error(f"Root path does not exist: {path}")
                    return False
                
                # Check if already added
                uri = self._path_to_uri(root_path)
                for existing in self._roots:
                    if existing.uri == uri:
                        logger.info(f"Root already exists: {uri}")
                        return True
                
                # Request consent if required
                if self._require_consent and uri not in self._consent_cache:
                    consent = await self._request_consent(root_path, name)
                    self._consent_cache[uri] = consent
                    if not consent:
                        logger.info(f"User denied consent for root: {path}")
                        return False
                
                # Add the root
                root = Root(uri=uri, name=name or root_path.name)
                self._roots.append(root)
                logger.info(f"Added root: {uri} (name: {root.name})")
                
                # Notify listeners
                await self._notify_listeners()
                
                return True
                
            except Exception as e:
                logger.error(f"Error adding root '{path}': {e}")
                return False
    
    async def remove_root(self, uri: str) -> bool:
        """Remove a root by URI."""
        async with self._lock:
            initial_count = len(self._roots)
            self._roots = [r for r in self._roots if r.uri != uri]
            
            if len(self._roots) < initial_count:
                logger.info(f"Removed root: {uri}")
                await self._notify_listeners()
                return True
            
            logger.warning(f"Root not found for removal: {uri}")
            return False
    
    async def list_roots(self) -> List[Root]:
        """Get the current list of roots."""
        async with self._lock:
            # Validate roots still exist and are accessible
            valid_roots = []
            for root in self._roots:
                try:
                    if root.path.exists():
                        valid_roots.append(root)
                    else:
                        logger.warning(f"Root no longer exists: {root.uri}")
                except Exception as e:
                    logger.error(f"Error validating root {root.uri}: {e}")
            
            # Update list if any were removed
            if len(valid_roots) < len(self._roots):
                self._roots = valid_roots
                await self._notify_listeners()
            
            return list(self._roots)
    
    async def _request_consent(self, path: Path, name: Optional[str]) -> bool:
        """
        Request user consent for exposing a root.
        
        For now, this is a placeholder that logs and auto-approves.
        In production, this should show a UI dialog.
        """
        logger.info(f"Consent requested for root: {path} (name: {name})")
        # TODO: Implement actual UI consent dialog
        # For now, auto-approve with warning
        logger.warning("Auto-approving root consent (implement UI dialog in production)")
        return True
    
    def get_capability(self) -> Dict[str, Any]:
        """Get the roots capability declaration for MCP."""
        return {
            "listChanged": True  # We support change notifications
        }
    
    async def validate_access(self, file_uri: str) -> bool:
        """
        Validate that a file URI is within allowed roots.
        
        Args:
            file_uri: File URI to validate
            
        Returns:
            True if access is allowed
        """
        try:
            parsed = urlparse(file_uri)
            if parsed.scheme != "file":
                return False
            
            # Convert URI to path
            if parsed.netloc:  # Windows
                file_path = Path(f"{parsed.netloc}{parsed.path}")
            else:
                file_path = Path(parsed.path)
            
            file_path = file_path.resolve()
            
            # Check if within any root
            for root in self._roots:
                try:
                    file_path.relative_to(root.path)
                    return True
                except ValueError:
                    continue
            
            logger.warning(f"File '{file_uri}' not within any allowed root")
            return False
            
        except Exception as e:
            logger.error(f"Error validating file access for '{file_uri}': {e}")
            return False


class RootsSecurityValidator:
    """Additional security validation for roots operations."""
    
    @staticmethod
    def validate_uri(uri: str) -> bool:
        """Validate that a URI is safe and well-formed."""
        try:
            parsed = urlparse(uri)
            
            # Only allow file:// scheme
            if parsed.scheme != "file":
                return False
            
            # Check for suspicious patterns
            suspicious_patterns = [
                "..",  # Path traversal
                "~",   # Home directory expansion (should be resolved)
                "${",  # Variable expansion
                "%",   # URL encoding (should be decoded)
            ]
            
            for pattern in suspicious_patterns:
                if pattern in parsed.path:
                    logger.warning(f"Suspicious pattern '{pattern}' in URI: {uri}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"URI validation error: {e}")
            return False
    
    @staticmethod
    def validate_path_traversal(base_path: Path, target_path: Path) -> bool:
        """
        Validate that target_path is within base_path (no traversal).
        
        Returns:
            True if target is safely within base
        """
        try:
            base = base_path.resolve()
            target = target_path.resolve()
            
            # Check if target is within base
            target.relative_to(base)
            return True
            
        except ValueError:
            # relative_to raises ValueError if target is not within base
            return False
        except Exception as e:
            logger.error(f"Path traversal validation error: {e}")
            return False