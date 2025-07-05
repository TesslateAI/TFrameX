---
sidebar_position: 5
title: Session Management
---

# Session Management

TFrameX Enterprise provides secure session management with support for multiple backends, concurrent session control, and advanced security features.

## Overview

Session management features include:
- **Multiple Storage Backends** - Memory, Redis, Database
- **Session Security** - Encryption, secure cookies, CSRF protection
- **Concurrent Session Control** - Limit sessions per user
- **Session Lifecycle** - Creation, refresh, expiration, revocation
- **Activity Tracking** - Monitor session usage and detect anomalies
- **Cross-Device Sessions** - Manage sessions across multiple devices

## Basic Configuration

```python
from tframex.enterprise.security.session import SessionManager

# Configure session manager
session_config = {
    "backend": "redis",  # memory, redis, database
    "timeout": 3600,     # 1 hour
    "refresh_enabled": True,
    "refresh_threshold": 300,  # Refresh if < 5 minutes left
    
    # Security settings
    "secure_cookies": True,
    "httponly": True,
    "samesite": "strict",
    "csrf_protection": True,
    
    # Limits
    "max_sessions_per_user": 5,
    "max_idle_time": 1800,  # 30 minutes
    
    # Storage settings
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 1,
        "password": os.environ.get("REDIS_PASSWORD")
    }
}

session_manager = SessionManager(session_config)

# Add to enterprise app
app = EnterpriseApp(
    enterprise_config={
        "session": session_config
    }
)
```

## Session Lifecycle

### Creating Sessions

```python
from tframex.enterprise.security.session import Session

# Create session after authentication
async def create_user_session(user, request):
    session = await session_manager.create_session(
        user_id=user.id,
        
        # Session metadata
        metadata={
            "ip_address": request.client.host,
            "user_agent": request.headers.get("User-Agent"),
            "device_id": request.headers.get("X-Device-ID"),
            "auth_method": "jwt",
            "mfa_verified": True
        },
        
        # Custom data
        data={
            "theme": "dark",
            "language": "en",
            "timezone": "UTC"
        },
        
        # Security settings
        bind_to_ip=True,
        require_mfa_for_sensitive=True
    )
    
    return session
```

### Session Validation

```python
# Validate session on each request
async def validate_request_session(request):
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        return None
    
    # Validate session
    session = await session_manager.validate_session(
        session_id=session_id,
        
        # Additional validation
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent")
    )
    
    if not session:
        # Invalid or expired session
        return None
    
    # Update last activity
    await session_manager.touch_session(session_id)
    
    return session
```

### Session Refresh

```python
# Automatic session refresh
async def refresh_session_if_needed(session):
    remaining_time = session.expires_at - datetime.utcnow()
    
    if remaining_time.total_seconds() < session_config["refresh_threshold"]:
        # Refresh session
        new_session = await session_manager.refresh_session(
            session_id=session.id,
            extend_by=session_config["timeout"]
        )
        
        # Update cookie
        response.set_cookie(
            "session_id",
            new_session.id,
            max_age=session_config["timeout"],
            secure=True,
            httponly=True
        )
        
        return new_session
    
    return session

# Manual refresh with re-authentication
async def refresh_with_reauth(session, password):
    # Verify password
    user = await get_user(session.user_id)
    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid password")
    
    # Create fresh session
    new_session = await session_manager.create_fresh_session(
        user_id=user.id,
        previous_session_id=session.id,
        inherit_data=True
    )
    
    # Revoke old session
    await session_manager.revoke_session(session.id)
    
    return new_session
```

### Session Revocation

```python
# Revoke single session
async def logout(session_id):
    await session_manager.revoke_session(
        session_id=session_id,
        reason="user_logout"
    )
    
    # Clear cookie
    response.delete_cookie("session_id")

# Revoke all user sessions
async def logout_all_devices(user_id):
    sessions = await session_manager.get_user_sessions(user_id)
    
    for session in sessions:
        await session_manager.revoke_session(
            session_id=session.id,
            reason="logout_all_devices"
        )
    
    # Notify user
    await send_notification(
        user_id,
        "All sessions have been terminated"
    )

# Selective revocation
async def revoke_suspicious_sessions(user_id):
    sessions = await session_manager.get_user_sessions(user_id)
    
    for session in sessions:
        risk_score = await calculate_session_risk(session)
        
        if risk_score > 0.7:
            await session_manager.revoke_session(
                session_id=session.id,
                reason="suspicious_activity"
            )
```

## Storage Backends

### Redis Backend

```python
from tframex.enterprise.security.session import RedisSessionStore

redis_store = RedisSessionStore(
    host="localhost",
    port=6379,
    db=1,
    password=os.environ.get("REDIS_PASSWORD"),
    
    # Connection pool
    max_connections=50,
    
    # Key settings
    key_prefix="tframex:session:",
    
    # Performance
    socket_keepalive=True,
    socket_timeout=5
)

session_manager = SessionManager(
    store=redis_store,
    **session_config
)
```

### Database Backend

```python
from tframex.enterprise.security.session import DatabaseSessionStore

db_store = DatabaseSessionStore(
    connection_string=os.environ["DATABASE_URL"],
    
    # Table configuration
    table_name="user_sessions",
    
    # Performance
    pool_size=20,
    
    # Cleanup
    auto_cleanup=True,
    cleanup_interval=3600  # Clean expired sessions hourly
)

# Database schema
"""
CREATE TABLE user_sessions (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    data JSONB,
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP,
    revoke_reason VARCHAR(255),
    
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_last_activity (last_activity)
);
"""
```

### Memory Backend (Development)

```python
from tframex.enterprise.security.session import MemorySessionStore

memory_store = MemorySessionStore(
    # Limits
    max_sessions=10000,
    
    # Cleanup
    cleanup_interval=300,  # 5 minutes
    
    # Persistence (optional)
    persist_to_file="sessions.pkl",
    persist_interval=60
)
```

## Advanced Session Features

### Device Fingerprinting

```python
from tframex.enterprise.security.session import DeviceFingerprint

# Create device fingerprint
async def create_device_fingerprint(request):
    fingerprint = DeviceFingerprint(
        user_agent=request.headers.get("User-Agent"),
        accept_language=request.headers.get("Accept-Language"),
        accept_encoding=request.headers.get("Accept-Encoding"),
        
        # JavaScript-collected data
        screen_resolution=request.json.get("screen_resolution"),
        timezone=request.json.get("timezone"),
        canvas_fingerprint=request.json.get("canvas_fp"),
        webgl_fingerprint=request.json.get("webgl_fp"),
        
        # Additional signals
        plugins=request.json.get("plugins", []),
        fonts=request.json.get("fonts", [])
    )
    
    return fingerprint.calculate_hash()

# Bind session to device
session = await session_manager.create_session(
    user_id=user.id,
    device_fingerprint=device_fingerprint,
    bind_to_device=True
)

# Validate device on each request
is_valid = await session_manager.validate_device(
    session_id=session_id,
    current_fingerprint=current_device_fingerprint
)
```

### Concurrent Session Control

```python
from tframex.enterprise.security.session import ConcurrentSessionPolicy

# Configure concurrent session policy
concurrent_policy = ConcurrentSessionPolicy(
    max_sessions_per_user=3,
    
    # Strategy when limit exceeded
    strategy="revoke_oldest",  # or "deny_new", "ask_user"
    
    # Device-based limits
    max_sessions_per_device=1,
    
    # Role-based limits
    role_limits={
        "basic": 1,
        "premium": 3,
        "enterprise": 10
    }
)

session_manager.set_concurrent_policy(concurrent_policy)

# Handle limit exceeded
@session_manager.on_session_limit_exceeded
async def handle_session_limit(user_id, existing_sessions):
    if concurrent_policy.strategy == "ask_user":
        # Send notification to user
        await notify_user_session_limit(
            user_id,
            existing_sessions,
            action_required=True
        )
    elif concurrent_policy.strategy == "revoke_oldest":
        # Revoke oldest session
        oldest = min(existing_sessions, key=lambda s: s.created_at)
        await session_manager.revoke_session(oldest.id)
```

### Session Sharing

```python
# Share session data across services
class SessionSharing:
    def __init__(self, session_manager, encryption_key):
        self.session_manager = session_manager
        self.encryption_key = encryption_key
    
    async def export_session_token(self, session_id):
        """Export encrypted session token for service-to-service auth."""
        session = await self.session_manager.get_session(session_id)
        
        token_data = {
            "session_id": session.id,
            "user_id": session.user_id,
            "expires_at": session.expires_at.isoformat(),
            "permissions": session.metadata.get("permissions", [])
        }
        
        # Encrypt token
        encrypted_token = encrypt_data(
            json.dumps(token_data),
            self.encryption_key
        )
        
        return base64.b64encode(encrypted_token).decode()
    
    async def import_session_token(self, token):
        """Import and validate session token from another service."""
        try:
            encrypted_data = base64.b64decode(token)
            token_data = json.loads(
                decrypt_data(encrypted_data, self.encryption_key)
            )
            
            # Validate session still active
            session = await self.session_manager.get_session(
                token_data["session_id"]
            )
            
            if session and session.is_valid():
                return session
            
        except Exception as e:
            logger.warning(f"Invalid session token: {e}")
        
        return None
```

## Session Security

### CSRF Protection

```python
from tframex.enterprise.security.session import CSRFProtection

# Configure CSRF protection
csrf_protection = CSRFProtection(
    token_length=32,
    token_name="csrf_token",
    header_name="X-CSRF-Token",
    
    # Double submit cookie
    use_double_submit=True,
    
    # Excluded paths
    exclude_paths=["/api/webhook", "/health"],
    
    # Token rotation
    rotate_token_on_login=True
)

session_manager.enable_csrf_protection(csrf_protection)

# Generate CSRF token
@app.route("/api/csrf-token")
async def get_csrf_token(session):
    token = await csrf_protection.generate_token(session.id)
    return {"csrf_token": token}

# Validate CSRF token
@csrf_protection.protect
async def protected_endpoint(request):
    # CSRF token automatically validated
    return {"status": "success"}
```

### Session Encryption

```python
from tframex.enterprise.security.session import SessionEncryption

# Configure session encryption
encryption = SessionEncryption(
    # Encryption settings
    algorithm="AES-256-GCM",
    key=os.environ["SESSION_ENCRYPTION_KEY"],
    
    # Key rotation
    enable_key_rotation=True,
    rotation_interval_days=30,
    
    # Encrypt specific fields
    encrypted_fields=["data", "metadata.sensitive"]
)

session_manager.enable_encryption(encryption)

# Encrypted session data
session = await session_manager.create_session(
    user_id=user.id,
    data={
        "api_key": "sensitive_key",  # Will be encrypted
        "preferences": {"theme": "dark"}  # Will be encrypted
    }
)
```

### Session Hijacking Prevention

```python
from tframex.enterprise.security.session import AntiHijacking

# Configure anti-hijacking measures
anti_hijacking = AntiHijacking(
    # IP binding
    bind_to_ip=True,
    allow_ip_change=False,
    
    # User agent validation
    validate_user_agent=True,
    user_agent_similarity_threshold=0.8,
    
    # Fingerprint validation
    validate_fingerprint=True,
    
    # Behavioral analysis
    analyze_behavior=True,
    behavior_change_threshold=0.7
)

session_manager.enable_anti_hijacking(anti_hijacking)

# Monitor for hijacking attempts
@anti_hijacking.on_suspicious_activity
async def handle_suspicious_activity(session, reason, risk_score):
    if risk_score > 0.8:
        # High risk - immediate action
        await session_manager.revoke_session(session.id)
        await notify_user_security_alert(session.user_id, reason)
    elif risk_score > 0.5:
        # Medium risk - require re-authentication
        await session_manager.flag_session_for_reauth(session.id)
```

## Session Monitoring

### Activity Tracking

```python
from tframex.enterprise.security.session import SessionActivityTracker

# Track session activity
activity_tracker = SessionActivityTracker(session_manager)

# Record activity
await activity_tracker.record_activity(
    session_id=session.id,
    activity_type="api_call",
    details={
        "endpoint": "/api/agents/execute",
        "method": "POST",
        "response_time_ms": 234
    }
)

# Get session analytics
analytics = await activity_tracker.get_session_analytics(session.id)
print(f"Total activities: {analytics.total_activities}")
print(f"Average response time: {analytics.avg_response_time_ms}ms")
print(f"Most used endpoint: {analytics.most_used_endpoint}")

# Detect anomalies
anomalies = await activity_tracker.detect_anomalies(
    session_id=session.id,
    baseline_sessions=10
)

if anomalies:
    await handle_session_anomalies(session.id, anomalies)
```

### Session Metrics

```python
from tframex.enterprise.security.session import SessionMetrics

metrics = SessionMetrics(session_manager)

# Real-time metrics
current_metrics = await metrics.get_current_metrics()
print(f"Active sessions: {current_metrics.active_sessions}")
print(f"Sessions created (1h): {current_metrics.sessions_created_1h}")
print(f"Sessions expired (1h): {current_metrics.sessions_expired_1h}")
print(f"Average session duration: {current_metrics.avg_duration_minutes}m")

# User metrics
user_metrics = await metrics.get_user_metrics(user_id)
print(f"Active sessions: {user_metrics.active_sessions}")
print(f"Total sessions (30d): {user_metrics.total_sessions_30d}")
print(f"Average session duration: {user_metrics.avg_duration_minutes}m")

# Export metrics for monitoring
prometheus_metrics = await metrics.export_prometheus_format()
```

## Session Management UI

### Admin Interface

```python
from tframex.enterprise.security.session import SessionAdminInterface

# Create admin interface
admin_interface = SessionAdminInterface(
    session_manager=session_manager,
    require_permission="admin:sessions"
)

# List all active sessions
@app.route("/admin/sessions")
@require_permission("admin:sessions:read")
async def list_sessions(request):
    filters = {
        "user_id": request.args.get("user_id"),
        "ip_address": request.args.get("ip_address"),
        "active": True
    }
    
    sessions = await admin_interface.list_sessions(
        filters=filters,
        page=int(request.args.get("page", 1)),
        per_page=50
    )
    
    return {
        "sessions": sessions,
        "total": await admin_interface.count_sessions(filters)
    }

# Terminate session
@app.route("/admin/sessions/<session_id>/terminate", methods=["POST"])
@require_permission("admin:sessions:terminate")
async def terminate_session(session_id, request):
    reason = request.json.get("reason", "admin_termination")
    
    await admin_interface.terminate_session(
        session_id=session_id,
        terminated_by=request.user.id,
        reason=reason
    )
    
    return {"status": "terminated"}
```

### User Self-Service

```python
# User session management
@app.route("/account/sessions")
@require_authentication
async def my_sessions(request, user):
    sessions = await session_manager.get_user_sessions(
        user_id=user.id,
        include_expired=False
    )
    
    # Enhance with device info
    for session in sessions:
        session.device_info = parse_user_agent(session.user_agent)
        session.location = await get_location_from_ip(session.ip_address)
    
    return {"sessions": sessions}

@app.route("/account/sessions/<session_id>/revoke", methods=["POST"])
@require_authentication
async def revoke_my_session(session_id, request, user):
    # Verify session belongs to user
    session = await session_manager.get_session(session_id)
    
    if session.user_id != user.id:
        raise AuthorizationError("Cannot revoke another user's session")
    
    await session_manager.revoke_session(
        session_id=session_id,
        reason="user_revoked"
    )
    
    return {"status": "revoked"}
```

## Testing Sessions

```python
import pytest
from tframex.enterprise.testing import SessionTestHarness

@pytest.fixture
def session_harness():
    return SessionTestHarness()

async def test_session_lifecycle(session_harness):
    # Create session
    session = await session_harness.create_test_session(
        user_id="test_user",
        metadata={"test": True}
    )
    
    assert session.id is not None
    assert session.is_valid()
    
    # Validate session
    validated = await session_harness.validate_session(session.id)
    assert validated is not None
    
    # Expire session
    await session_harness.expire_session(session.id)
    validated = await session_harness.validate_session(session.id)
    assert validated is None

async def test_concurrent_sessions(session_harness):
    # Test session limits
    sessions = []
    
    # Create max sessions
    for i in range(3):
        session = await session_harness.create_test_session(
            user_id="test_user"
        )
        sessions.append(session)
    
    # Try to create one more
    with pytest.raises(SessionLimitExceeded):
        await session_harness.create_test_session(
            user_id="test_user"
        )
```

## Best Practices

### 1. Secure Session Configuration

```python
# Production session configuration
PRODUCTION_SESSION_CONFIG = {
    "backend": "redis",
    "timeout": 3600,  # 1 hour
    "secure_cookies": True,
    "httponly": True,
    "samesite": "strict",
    "csrf_protection": True,
    
    # Security
    "bind_to_ip": True,
    "validate_user_agent": True,
    "encrypt_data": True,
    
    # Limits
    "max_sessions_per_user": 3,
    "max_idle_time": 1800  # 30 minutes
}
```

### 2. Session Hygiene

```python
# Regular cleanup
async def cleanup_sessions():
    # Remove expired sessions
    expired_count = await session_manager.cleanup_expired_sessions()
    logger.info(f"Cleaned up {expired_count} expired sessions")
    
    # Remove idle sessions
    idle_count = await session_manager.cleanup_idle_sessions(
        idle_threshold=timedelta(hours=2)
    )
    logger.info(f"Cleaned up {idle_count} idle sessions")
    
    # Analyze orphaned sessions
    orphaned = await session_manager.find_orphaned_sessions()
    if orphaned:
        logger.warning(f"Found {len(orphaned)} orphaned sessions")

# Schedule cleanup
scheduler.add_job(cleanup_sessions, "interval", hours=1)
```

### 3. Session Security Monitoring

```python
# Monitor session security
async def monitor_session_security():
    # Check for suspicious patterns
    suspicious_patterns = [
        # Rapid session creation
        await check_rapid_session_creation(),
        
        # Geographic anomalies
        await check_geographic_anomalies(),
        
        # Device switching
        await check_device_switching(),
        
        # Unusual activity patterns
        await check_activity_patterns()
    ]
    
    for pattern in suspicious_patterns:
        if pattern.risk_score > 0.7:
            await trigger_security_alert(pattern)
```

## Next Steps

- [Security Hardening](hardening) - Additional security measures
- [Monitoring](../monitoring) - Monitor session metrics
- [Compliance](compliance) - Session compliance requirements
- [Incident Response](incident-response) - Handle session security incidents