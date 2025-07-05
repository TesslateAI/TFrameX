---
sidebar_position: 2
title: Authentication
---

# Authentication

TFrameX Enterprise supports multiple authentication providers to integrate with your existing security infrastructure.

## Authentication Providers

### JWT (JSON Web Tokens)

JWT provides stateless authentication ideal for distributed systems.

```python
from tframex.enterprise.security.auth import JWTProvider

# Configure JWT provider
jwt_provider = JWTProvider(
    secret_key="your-secret-key",  # Use environment variable in production
    algorithm="HS256",  # or RS256 for RSA
    token_expiry=3600,  # 1 hour
    refresh_enabled=True,
    refresh_expiry=86400  # 24 hours
)

# Add to enterprise app
app = EnterpriseApp(
    enterprise_config={
        "security": {
            "authentication": {
                "providers": [jwt_provider.to_config()]
            }
        }
    }
)
```

#### Advanced JWT Configuration

```python
# RSA-based JWT (more secure)
jwt_provider = JWTProvider(
    algorithm="RS256",
    public_key_path="/keys/public.pem",
    private_key_path="/keys/private.pem",
    issuer="https://auth.example.com",
    audience="tframex-api",
    require_claims=["sub", "email", "roles"]
)

# Custom claims validation
def validate_custom_claims(claims):
    if "department" not in claims:
        return False
    if claims.get("security_clearance", 0) < 2:
        return False
    return True

jwt_provider.add_claims_validator(validate_custom_claims)
```

#### Token Generation

```python
# Generate tokens for users
from tframex.enterprise.security.auth import generate_jwt_token

token = generate_jwt_token(
    user_id="user123",
    email="user@example.com",
    roles=["operator", "developer"],
    custom_claims={
        "department": "engineering",
        "security_clearance": 3
    }
)

# Generate refresh token
refresh_token = generate_refresh_token(user_id="user123")
```

### OAuth2

Integrate with OAuth2 providers like Google, GitHub, or your corporate SSO.

```python
from tframex.enterprise.security.auth import OAuth2Provider

# Configure OAuth2
oauth_provider = OAuth2Provider(
    client_id="your-client-id",
    client_secret="your-client-secret",
    authorize_url="https://oauth.example.com/authorize",
    token_url="https://oauth.example.com/token",
    userinfo_url="https://oauth.example.com/userinfo",
    scopes=["openid", "email", "profile"],
    redirect_uri="https://your-app.com/callback"
)
```

#### OAuth2 Flow Implementation

```python
# 1. Initiate OAuth flow
@app.route("/login/oauth")
async def oauth_login():
    auth_url = oauth_provider.get_authorization_url(
        state="random-state-token"
    )
    return redirect(auth_url)

# 2. Handle callback
@app.route("/callback")
async def oauth_callback(request):
    code = request.args.get("code")
    state = request.args.get("state")
    
    # Verify state and exchange code for token
    token_data = await oauth_provider.exchange_code(code, state)
    
    # Get user info
    user_info = await oauth_provider.get_user_info(token_data["access_token"])
    
    # Create session
    session = await app.create_session(user_info)
    
    return {"status": "authenticated", "session_id": session.id}
```

#### Corporate SSO Integration

```python
# Example: Okta integration
okta_provider = OAuth2Provider(
    client_id=os.environ["OKTA_CLIENT_ID"],
    client_secret=os.environ["OKTA_CLIENT_SECRET"],
    authorize_url=f"https://{OKTA_DOMAIN}/oauth2/v1/authorize",
    token_url=f"https://{OKTA_DOMAIN}/oauth2/v1/token",
    userinfo_url=f"https://{OKTA_DOMAIN}/oauth2/v1/userinfo",
    scopes=["openid", "email", "profile", "groups"],
    
    # Map Okta groups to TFrameX roles
    group_role_mapping={
        "Engineering": "developer",
        "Operations": "operator",
        "Management": "admin"
    }
)
```

### API Key Authentication

Simple key-based authentication for programmatic access.

```python
from tframex.enterprise.security.auth import APIKeyProvider

# Configure API key provider
api_key_provider = APIKeyProvider(
    header_name="X-API-Key",  # or custom header
    query_param="api_key",    # alternative: URL parameter
    key_length=32,
    key_prefix="tfx_",        # Optional prefix for keys
    
    # Optional: External validation
    validate_url="https://api.example.com/validate",
    cache_validation=True,
    cache_ttl=300
)
```

#### API Key Management

```python
from tframex.enterprise.security.auth import APIKeyManager

key_manager = APIKeyManager(storage_backend=app.storage)

# Generate new API key
new_key = await key_manager.create_key(
    user_id="user123",
    name="Production API Key",
    permissions=["agent:execute", "tool:read"],
    expires_at=datetime.now() + timedelta(days=90),
    metadata={
        "environment": "production",
        "service": "data-pipeline"
    }
)

# List user's API keys
keys = await key_manager.list_keys(user_id="user123")

# Revoke API key
await key_manager.revoke_key(key_id="key123")

# Rotate API key
new_key = await key_manager.rotate_key(old_key_id="key123")
```

### Basic Authentication

Username/password authentication with secure storage.

```python
from tframex.enterprise.security.auth import BasicAuthProvider

# Configure basic auth
basic_provider = BasicAuthProvider(
    realm="TFrameX Enterprise",
    hash_algorithm="bcrypt",  # or "scrypt", "argon2"
    
    # Password requirements
    min_password_length=12,
    require_uppercase=True,
    require_lowercase=True,
    require_numbers=True,
    require_special=True,
    
    # Security settings
    max_login_attempts=5,
    lockout_duration=900,  # 15 minutes
    password_history=5     # Prevent reuse of last 5 passwords
)
```

#### User Management

```python
from tframex.enterprise.security.auth import UserManager

user_manager = UserManager(
    auth_provider=basic_provider,
    storage_backend=app.storage
)

# Create user
user = await user_manager.create_user(
    username="john.doe",
    email="john@example.com",
    password="SecurePassword123!",
    roles=["developer"],
    metadata={
        "department": "Engineering",
        "employee_id": "EMP123"
    }
)

# Update password
await user_manager.update_password(
    user_id=user.id,
    old_password="OldPassword123!",
    new_password="NewPassword456!"
)

# Password reset flow
reset_token = await user_manager.initiate_password_reset(email="john@example.com")
# Send reset_token via email
await user_manager.complete_password_reset(reset_token, new_password="ResetPassword789!")
```

## Multi-Factor Authentication (MFA)

Add an extra layer of security with MFA.

```python
from tframex.enterprise.security.auth import MFAProvider

# Configure MFA
mfa_provider = MFAProvider(
    methods=["totp", "sms", "email"],
    required_for_roles=["admin", "operator"],
    grace_period=86400,  # 24 hours after first login
    backup_codes_count=10
)

# Add MFA to authentication flow
app.add_authentication_middleware(mfa_provider)
```

### TOTP (Time-based One-Time Password)

```python
# Setup TOTP for user
from tframex.enterprise.security.auth import setup_totp

secret, qr_code = await setup_totp(
    user_id="user123",
    app_name="TFrameX Enterprise"
)

# Display QR code to user
# User scans with authenticator app

# Verify TOTP code
is_valid = await verify_totp(
    user_id="user123",
    code="123456"
)
```

## Authentication Middleware

Protect your endpoints with authentication middleware.

```python
from tframex.enterprise.security.middleware import AuthenticationMiddleware

# Configure middleware
auth_middleware = AuthenticationMiddleware(
    providers=[jwt_provider, api_key_provider],
    exempt_paths=["/health", "/metrics"],
    
    # Optional: Custom authentication logic
    custom_authenticator=custom_auth_function
)

# Apply to app
app.add_middleware(auth_middleware)
```

### Protecting Endpoints

```python
from tframex.enterprise.security.decorators import require_authentication

@require_authentication
async def protected_endpoint(request, user):
    """This endpoint requires authentication."""
    return {"message": f"Hello {user.username}"}

# With specific authentication method
@require_authentication(methods=["jwt"])
async def jwt_only_endpoint(request, user):
    """This endpoint only accepts JWT authentication."""
    pass

# With custom validation
@require_authentication(validator=lambda user: user.role == "admin")
async def admin_only_endpoint(request, user):
    """This endpoint requires admin authentication."""
    pass
```

## Session Management

Manage user sessions across authentication providers.

```python
from tframex.enterprise.security.session import SessionManager

# Configure session manager
session_manager = SessionManager(
    backend="redis",  # or "memory", "database"
    timeout=3600,     # 1 hour
    refresh_enabled=True,
    max_sessions_per_user=5,
    
    # Security settings
    secure_cookies=True,
    httponly=True,
    samesite="strict"
)

# Create session after authentication
session = await session_manager.create_session(
    user_id=user.id,
    metadata={
        "ip_address": request.client.host,
        "user_agent": request.headers.get("User-Agent"),
        "auth_method": "jwt"
    }
)

# Validate session
is_valid = await session_manager.validate_session(session_id)

# Refresh session
new_session = await session_manager.refresh_session(session_id)

# Revoke session
await session_manager.revoke_session(session_id)

# Revoke all user sessions
await session_manager.revoke_all_sessions(user_id)
```

## Authentication Events

Monitor and respond to authentication events.

```python
from tframex.enterprise.security.events import AuthenticationEventHandler

# Configure event handler
auth_events = AuthenticationEventHandler()

@auth_events.on("login_success")
async def handle_login_success(event):
    # Log successful login
    await audit_logger.log(
        event_type="authentication",
        user_id=event.user_id,
        details={"method": event.auth_method}
    )

@auth_events.on("login_failure")
async def handle_login_failure(event):
    # Track failed attempts
    await security_monitor.track_failed_login(
        ip_address=event.ip_address,
        username=event.username
    )
    
    # Block after threshold
    if event.failure_count > 5:
        await ip_blocker.block(event.ip_address, duration=3600)

@auth_events.on("token_expired")
async def handle_token_expired(event):
    # Clean up expired sessions
    await session_manager.cleanup_expired()
```

## Authentication Best Practices

### 1. Secure Token Storage

```python
# Never store tokens in plain text
# Use secure storage with encryption
from tframex.enterprise.security.storage import SecureTokenStore

token_store = SecureTokenStore(
    encryption_key=os.environ["ENCRYPTION_KEY"],
    key_rotation_interval=2592000  # 30 days
)

# Store token securely
await token_store.store(user_id, token, encrypted=True)

# Retrieve and decrypt
token = await token_store.retrieve(user_id)
```

### 2. Rate Limiting

```python
from tframex.enterprise.security.ratelimit import AuthRateLimiter

rate_limiter = AuthRateLimiter(
    max_attempts=5,
    window_seconds=300,  # 5 minutes
    
    # Progressive delays
    delay_after_failure=[1, 2, 5, 10, 30]  # seconds
)

@rate_limiter.protect
async def login(username, password):
    # Rate-limited login logic
    pass
```

### 3. Secure Password Policies

```python
from tframex.enterprise.security.passwords import PasswordPolicy

password_policy = PasswordPolicy(
    min_length=12,
    max_length=128,
    require_uppercase=True,
    require_lowercase=True,
    require_numbers=True,
    require_special=True,
    
    # Additional rules
    prevent_common_passwords=True,
    prevent_user_info_in_password=True,
    check_password_breach=True  # Check against haveibeenpwned
)

# Validate password
is_valid, errors = password_policy.validate(
    password="MySecurePass123!",
    username="john.doe",
    email="john@example.com"
)
```

### 4. Authentication Logging

```python
# Log all authentication attempts
auth_logger = AuthenticationLogger(
    log_successful=True,
    log_failed=True,
    log_token_refresh=True,
    
    # Sensitive data handling
    mask_passwords=True,
    mask_tokens=True,
    
    # Include context
    include_ip_address=True,
    include_user_agent=True,
    include_geo_location=True
)
```

## Testing Authentication

```python
import pytest
from tframex.enterprise.testing import AuthenticationTestClient

@pytest.fixture
def auth_client():
    return AuthenticationTestClient(app)

async def test_jwt_authentication(auth_client):
    # Test successful authentication
    token = await auth_client.authenticate_jwt(
        username="test_user",
        password="test_password"
    )
    assert token is not None
    
    # Test token validation
    is_valid = await auth_client.validate_token(token)
    assert is_valid
    
    # Test invalid token
    is_valid = await auth_client.validate_token("invalid_token")
    assert not is_valid

async def test_api_key_authentication(auth_client):
    # Create API key
    api_key = await auth_client.create_api_key(
        user_id="test_user",
        permissions=["read"]
    )
    
    # Test authentication with API key
    result = await auth_client.authenticate_api_key(api_key)
    assert result.authenticated
    assert result.user_id == "test_user"
```

## Troubleshooting

### Common Issues

1. **JWT Token Validation Fails**
   ```python
   # Check token expiry
   decoded = jwt.decode(token, options={"verify_signature": False})
   print(f"Token expires at: {decoded['exp']}")
   
   # Verify secret key matches
   print(f"Using secret key: {jwt_provider.secret_key[:10]}...")
   ```

2. **OAuth2 Redirect Issues**
   ```python
   # Ensure redirect URI is registered
   print(f"Redirect URI: {oauth_provider.redirect_uri}")
   
   # Check state parameter
   print(f"Expected state: {session['oauth_state']}")
   print(f"Received state: {request.args.get('state')}")
   ```

3. **Session Timeout**
   ```python
   # Check session configuration
   print(f"Session timeout: {session_manager.timeout}")
   print(f"Refresh enabled: {session_manager.refresh_enabled}")
   
   # Monitor active sessions
   active_sessions = await session_manager.get_active_sessions()
   print(f"Active sessions: {len(active_sessions)}")
   ```

## Next Steps

- [Authorization](authorization) - Configure RBAC and permissions
- [Audit Logging](audit) - Set up compliance logging
- [Session Management](sessions) - Advanced session configuration
- [Security Hardening](hardening) - Additional security measures