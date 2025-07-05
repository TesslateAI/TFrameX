"""
Authentication Framework

This module provides a comprehensive authentication system with support
for multiple authentication providers including OAuth2, API keys,
basic authentication, and JWT tokens.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

try:
    import jwt
    import httpx
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

from ..models import User

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Exception raised when credentials are invalid."""
    pass


class ExpiredTokenError(AuthenticationError):
    """Exception raised when token has expired."""
    pass


class InsufficientPrivilegesError(AuthenticationError):
    """Exception raised when user lacks required privileges."""
    pass


@dataclass
class AuthenticationResult:
    """
    Result of an authentication attempt.
    """
    success: bool
    user: Optional[User] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AuthenticationProvider(ABC):
    """
    Abstract base class for authentication providers.
    
    Authentication providers handle the verification of user credentials
    and return user information upon successful authentication.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize authentication provider.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.name = config.get("name", self.__class__.__name__)
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthenticationResult:
        """
        Authenticate user with provided credentials.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            Authentication result
        """
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> AuthenticationResult:
        """
        Validate an authentication token.
        
        Args:
            token: Authentication token to validate
            
        Returns:
            Authentication result
        """
        pass
    
    async def initialize(self) -> None:
        """
        Initialize the authentication provider.
        
        This method is called when the provider is first loaded
        and can be used for setup tasks like connecting to external
        services or validating configuration.
        """
        pass
    
    async def shutdown(self) -> None:
        """
        Shutdown the authentication provider.
        
        This method is called when the application is shutting down
        and should clean up any resources used by the provider.
        """
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about this authentication provider.
        
        Returns:
            Provider information
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "enabled": self.enabled
        }


class APIKeyProvider(AuthenticationProvider):
    """
    API Key authentication provider.
    
    This provider authenticates users using API keys that are
    stored in the database and associated with user accounts.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize API key provider.
        
        Args:
            config: Configuration with keys:
                - storage: Storage backend for user/API key lookup
                - header_name: HTTP header name for API key (default: "X-API-Key")
                - key_length: Length of generated API keys
                - hash_algorithm: Algorithm for hashing keys
        """
        super().__init__(config)
        
        self.storage = config.get("storage")
        self.header_name = config.get("header_name", "X-API-Key")
        self.key_length = config.get("key_length", 32)
        self.hash_algorithm = config.get("hash_algorithm", "sha256")
        
        if not self.storage:
            raise ValueError("Storage backend is required for API key provider")
    
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthenticationResult:
        """
        Authenticate using API key.
        
        Args:
            credentials: Dictionary with 'api_key' field
            
        Returns:
            Authentication result
        """
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return AuthenticationResult(
                    success=False,
                    error="API key not provided"
                )
            
            return await self.validate_token(api_key)
            
        except Exception as e:
            logger.error(f"API key authentication failed: {e}")
            return AuthenticationResult(
                success=False,
                error=str(e)
            )
    
    async def validate_token(self, token: str) -> AuthenticationResult:
        """
        Validate API key token.
        
        Args:
            token: API key to validate
            
        Returns:
            Authentication result
        """
        try:
            # Hash the provided key
            key_hash = self._hash_key(token)
            
            # Look up user by API key hash
            users = await self.storage.select(
                "users",
                filters={"api_key_hash": key_hash, "is_active": True}
            )
            
            if not users:
                return AuthenticationResult(
                    success=False,
                    error="Invalid API key"
                )
            
            user_data = users[0]
            user = User.model_validate(user_data)
            
            return AuthenticationResult(
                success=True,
                user=user,
                metadata={
                    "auth_method": "api_key",
                    "key_hash": key_hash
                }
            )
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return AuthenticationResult(
                success=False,
                error=str(e)
            )
    
    def _hash_key(self, key: str) -> str:
        """
        Hash an API key using the configured algorithm.
        
        Args:
            key: API key to hash
            
        Returns:
            Hashed key
        """
        if self.hash_algorithm == "sha256":
            return hashlib.sha256(key.encode()).hexdigest()
        elif self.hash_algorithm == "sha512":
            return hashlib.sha512(key.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {self.hash_algorithm}")
    
    def generate_api_key(self) -> str:
        """
        Generate a new API key.
        
        Returns:
            Generated API key
        """
        return secrets.token_urlsafe(self.key_length)
    
    async def create_api_key(self, user_id: UUID) -> str:
        """
        Create a new API key for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Generated API key
        """
        api_key = self.generate_api_key()
        key_hash = self._hash_key(api_key)
        
        # Update user record with API key hash
        await self.storage.update(
            "users",
            str(user_id),
            {"api_key_hash": key_hash}
        )
        
        return api_key
    
    async def revoke_api_key(self, user_id: UUID) -> None:
        """
        Revoke a user's API key.
        
        Args:
            user_id: User ID
        """
        await self.storage.update(
            "users",
            str(user_id),
            {"api_key_hash": None}
        )


class BasicAuthProvider(AuthenticationProvider):
    """
    Basic HTTP authentication provider.
    
    This provider authenticates users using username/password
    combinations stored in the database.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize basic auth provider.
        
        Args:
            config: Configuration with keys:
                - storage: Storage backend for user lookup
                - password_salt: Salt for password hashing
                - iterations: PBKDF2 iterations for password hashing
        """
        super().__init__(config)
        
        if not CRYPTO_AVAILABLE:
            raise ImportError(
                "cryptography package is required for BasicAuthProvider. "
                "Install with: pip install cryptography"
            )
        
        self.storage = config.get("storage")
        self.password_salt = config.get("password_salt", "tframex_salt").encode()
        self.iterations = config.get("iterations", 100000)
        
        if not self.storage:
            raise ValueError("Storage backend is required for basic auth provider")
    
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthenticationResult:
        """
        Authenticate using username and password.
        
        Args:
            credentials: Dictionary with 'username' and 'password' fields
            
        Returns:
            Authentication result
        """
        try:
            username = credentials.get("username")
            password = credentials.get("password")
            
            if not username or not password:
                return AuthenticationResult(
                    success=False,
                    error="Username and password required"
                )
            
            # Look up user by username
            users = await self.storage.select(
                "users",
                filters={"username": username, "is_active": True}
            )
            
            if not users:
                return AuthenticationResult(
                    success=False,
                    error="Invalid username or password"
                )
            
            user_data = users[0]
            stored_hash = user_data.get("password_hash")
            
            if not stored_hash:
                return AuthenticationResult(
                    success=False,
                    error="Password authentication not available for this user"
                )
            
            # Verify password
            if not self._verify_password(password, stored_hash):
                return AuthenticationResult(
                    success=False,
                    error="Invalid username or password"
                )
            
            user = User.model_validate(user_data)
            
            return AuthenticationResult(
                success=True,
                user=user,
                metadata={
                    "auth_method": "basic_auth",
                    "username": username
                }
            )
            
        except Exception as e:
            logger.error(f"Basic authentication failed: {e}")
            return AuthenticationResult(
                success=False,
                error=str(e)
            )
    
    async def validate_token(self, token: str) -> AuthenticationResult:
        """
        Validate basic auth token (base64 encoded username:password).
        
        Args:
            token: Basic auth token
            
        Returns:
            Authentication result
        """
        try:
            # Decode base64 token
            decoded = base64.b64decode(token).decode('utf-8')
            username, password = decoded.split(':', 1)
            
            return await self.authenticate({
                "username": username,
                "password": password
            })
            
        except Exception as e:
            logger.error(f"Basic auth token validation failed: {e}")
            return AuthenticationResult(
                success=False,
                error="Invalid basic auth token"
            )
    
    def _hash_password(self, password: str) -> str:
        """
        Hash a password using PBKDF2.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.password_salt,
            iterations=self.iterations,
        )
        key = kdf.derive(password.encode())
        return base64.b64encode(key).decode()
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """
        Verify a password against stored hash.
        
        Args:
            password: Password to verify
            stored_hash: Stored password hash
            
        Returns:
            True if password is valid
        """
        try:
            computed_hash = self._hash_password(password)
            return hmac.compare_digest(computed_hash, stored_hash)
        except Exception:
            return False
    
    async def set_password(self, user_id: UUID, password: str) -> None:
        """
        Set a user's password.
        
        Args:
            user_id: User ID
            password: New password
        """
        password_hash = self._hash_password(password)
        await self.storage.update(
            "users",
            str(user_id),
            {"password_hash": password_hash}
        )


class JWTProvider(AuthenticationProvider):
    """
    JSON Web Token (JWT) authentication provider.
    
    This provider creates and validates JWT tokens for stateless
    authentication.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize JWT provider.
        
        Args:
            config: Configuration with keys:
                - secret_key: Secret key for signing JWTs
                - algorithm: JWT signing algorithm (default: HS256)
                - expiration: Token expiration time in seconds
                - issuer: JWT issuer
                - audience: JWT audience
        """
        super().__init__(config)
        
        if not CRYPTO_AVAILABLE:
            raise ImportError(
                "PyJWT package is required for JWTProvider. "
                "Install with: pip install PyJWT"
            )
        
        self.secret_key = config.get("secret_key")
        self.algorithm = config.get("algorithm", "HS256")
        self.expiration = config.get("expiration", 3600)  # 1 hour
        self.issuer = config.get("issuer", "tframex")
        self.audience = config.get("audience", "tframex-api")
        
        if not self.secret_key:
            raise ValueError("Secret key is required for JWT provider")
    
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthenticationResult:
        """
        This provider doesn't handle initial authentication,
        only token validation. Use other providers for login.
        """
        return AuthenticationResult(
            success=False,
            error="JWT provider only validates tokens"
        )
    
    async def validate_token(self, token: str) -> AuthenticationResult:
        """
        Validate JWT token.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Authentication result
        """
        try:
            # Decode and verify JWT
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience
            )
            
            # Extract user information
            user_id = payload.get("sub")
            username = payload.get("username")
            email = payload.get("email")
            
            if not user_id:
                return AuthenticationResult(
                    success=False,
                    error="Invalid token: missing user ID"
                )
            
            # Create user object from token claims
            user = User(
                id=UUID(user_id),
                username=username or "",
                email=email,
                is_active=True
            )
            
            return AuthenticationResult(
                success=True,
                user=user,
                metadata={
                    "auth_method": "jwt",
                    "token_claims": payload
                }
            )
            
        except jwt.ExpiredSignatureError:
            return AuthenticationResult(
                success=False,
                error="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            return AuthenticationResult(
                success=False,
                error=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"JWT validation failed: {e}")
            return AuthenticationResult(
                success=False,
                error=str(e)
            )
    
    def generate_token(self, user: User, additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a JWT token for a user.
        
        Args:
            user: User to generate token for
            additional_claims: Additional claims to include
            
        Returns:
            JWT token
        """
        now = datetime.utcnow()
        expiry = now + timedelta(seconds=self.expiration)
        
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "iat": int(now.timestamp()),
            "exp": int(expiry.timestamp()),
            "iss": self.issuer,
            "aud": self.audience
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


class OAuth2Provider(AuthenticationProvider):
    """
    OAuth 2.0 / OpenID Connect authentication provider.
    
    This provider handles OAuth2 authentication flows with
    external identity providers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OAuth2 provider.
        
        Args:
            config: Configuration with keys:
                - client_id: OAuth2 client ID
                - client_secret: OAuth2 client secret
                - issuer: OpenID Connect issuer URL
                - scopes: OAuth2 scopes to request
                - redirect_uri: OAuth2 redirect URI
        """
        super().__init__(config)
        
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.issuer = config.get("issuer")
        self.scopes = config.get("scopes", ["openid", "profile", "email"])
        self.redirect_uri = config.get("redirect_uri")
        
        # OpenID Connect endpoints (discovered from issuer)
        self.authorization_endpoint: Optional[str] = None
        self.token_endpoint: Optional[str] = None
        self.userinfo_endpoint: Optional[str] = None
        self.jwks_uri: Optional[str] = None
        
        if not all([self.client_id, self.client_secret, self.issuer]):
            raise ValueError(
                "client_id, client_secret, and issuer are required for OAuth2 provider"
            )
    
    async def initialize(self) -> None:
        """
        Initialize OAuth2 provider by discovering endpoints.
        """
        try:
            # Discover OpenID Connect configuration
            discovery_url = f"{self.issuer.rstrip('/')}/.well-known/openid_configuration"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(discovery_url)
                response.raise_for_status()
                
                config = response.json()
                self.authorization_endpoint = config["authorization_endpoint"]
                self.token_endpoint = config["token_endpoint"]
                self.userinfo_endpoint = config["userinfo_endpoint"]
                self.jwks_uri = config["jwks_uri"]
            
            logger.info(f"OAuth2 provider initialized for issuer: {self.issuer}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OAuth2 provider: {e}")
            raise
    
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthenticationResult:
        """
        Authenticate using OAuth2 authorization code.
        
        Args:
            credentials: Dictionary with 'authorization_code' field
            
        Returns:
            Authentication result
        """
        try:
            auth_code = credentials.get("authorization_code")
            if not auth_code:
                return AuthenticationResult(
                    success=False,
                    error="Authorization code required"
                )
            
            # Exchange authorization code for tokens
            token_data = await self._exchange_code_for_tokens(auth_code)
            
            # Get user info from userinfo endpoint
            user_info = await self._get_user_info(token_data["access_token"])
            
            # Create user object
            user = User(
                id=uuid4(),  # Generate new ID or map from provider ID
                username=user_info.get("preferred_username", user_info.get("email", "")),
                email=user_info.get("email"),
                is_active=True,
                metadata={
                    "oauth2_provider": self.issuer,
                    "oauth2_subject": user_info.get("sub")
                }
            )
            
            return AuthenticationResult(
                success=True,
                user=user,
                metadata={
                    "auth_method": "oauth2",
                    "tokens": token_data,
                    "user_info": user_info
                }
            )
            
        except Exception as e:
            logger.error(f"OAuth2 authentication failed: {e}")
            return AuthenticationResult(
                success=False,
                error=str(e)
            )
    
    async def validate_token(self, token: str) -> AuthenticationResult:
        """
        Validate OAuth2 access token.
        
        Args:
            token: Access token to validate
            
        Returns:
            Authentication result
        """
        try:
            # Get user info using access token
            user_info = await self._get_user_info(token)
            
            # Create user object
            user = User(
                id=uuid4(),  # Generate new ID or map from provider ID
                username=user_info.get("preferred_username", user_info.get("email", "")),
                email=user_info.get("email"),
                is_active=True,
                metadata={
                    "oauth2_provider": self.issuer,
                    "oauth2_subject": user_info.get("sub")
                }
            )
            
            return AuthenticationResult(
                success=True,
                user=user,
                metadata={
                    "auth_method": "oauth2_token",
                    "user_info": user_info
                }
            )
            
        except Exception as e:
            logger.error(f"OAuth2 token validation failed: {e}")
            return AuthenticationResult(
                success=False,
                error=str(e)
            )
    
    async def _exchange_code_for_tokens(self, auth_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            auth_code: Authorization code
            
        Returns:
            Token response
        """
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_endpoint,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            return response.json()
    
    async def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information using access token.
        
        Args:
            access_token: OAuth2 access token
            
        Returns:
            User information
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Get OAuth2 authorization URL for user redirect.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes)
        }
        
        if state:
            params["state"] = state
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.authorization_endpoint}?{query_string}"