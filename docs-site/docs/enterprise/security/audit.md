---
sidebar_position: 4
title: Audit Logging
---

# Audit Logging

TFrameX Enterprise provides comprehensive audit logging for compliance, security monitoring, and forensic analysis. Every significant action is logged with full context and tamper-proof storage.

## Overview

The audit logging system captures:
- **Authentication Events** - Login attempts, token generation, session creation
- **Authorization Events** - Permission checks, access grants/denials
- **Resource Access** - Agent execution, tool usage, data access
- **Configuration Changes** - System settings, role modifications
- **Security Events** - Suspicious activities, policy violations
- **Data Operations** - CRUD operations on sensitive data

## Basic Configuration

```python
from tframex.enterprise.security.audit import AuditLogger

# Configure audit logger
audit_config = {
    "enabled": True,
    "storage": "postgresql",  # or "s3", "elasticsearch"
    "retention_days": 90,
    "encryption": True,
    "compression": True,
    
    # Event filtering
    "events": {
        "authentication": True,
        "authorization": True,
        "resource_access": True,
        "configuration": True,
        "security": True,
        "data_operations": True
    },
    
    # Sensitive data handling
    "mask_sensitive_data": True,
    "sensitive_fields": ["password", "token", "api_key", "ssn", "credit_card"]
}

audit_logger = AuditLogger(audit_config)

# Add to enterprise app
app = EnterpriseApp(
    enterprise_config={
        "security": {
            "audit": audit_config
        }
    }
)
```

## Audit Event Structure

```python
from tframex.enterprise.security.audit import AuditEvent, AuditEventType, AuditOutcome

# Standard audit event
event = AuditEvent(
    # Required fields
    event_id="evt_123456789",
    event_type=AuditEventType.AUTHENTICATION,
    timestamp=datetime.utcnow(),
    
    # Actor information
    actor_id="user_123",
    actor_type="user",
    actor_name="john.doe@example.com",
    actor_ip="192.168.1.100",
    actor_user_agent="Mozilla/5.0...",
    
    # Action details
    action="login",
    resource_type="system",
    resource_id="main_app",
    
    # Outcome
    outcome=AuditOutcome.SUCCESS,
    
    # Additional context
    details={
        "auth_method": "jwt",
        "mfa_used": True,
        "session_id": "sess_abc123"
    },
    
    # Security context
    risk_score=0.2,
    threat_indicators=[]
)
```

## Logging Authentication Events

```python
from tframex.enterprise.security.audit import log_authentication_event

# Log successful login
await log_authentication_event(
    user_id="user_123",
    action="login",
    outcome="success",
    details={
        "auth_method": "oauth2",
        "provider": "google",
        "ip_address": request.client.host,
        "geo_location": "US-CA-San Francisco"
    }
)

# Log failed login
await log_authentication_event(
    user_id=None,  # Unknown user
    action="login",
    outcome="failure",
    details={
        "username_attempted": "admin",
        "failure_reason": "invalid_password",
        "ip_address": request.client.host,
        "attempt_number": 3
    }
)

# Log token operations
await log_authentication_event(
    user_id="user_123",
    action="token_refresh",
    outcome="success",
    details={
        "old_token_id": "tok_old123",
        "new_token_id": "tok_new456",
        "token_type": "jwt"
    }
)

# Log logout
await log_authentication_event(
    user_id="user_123",
    action="logout",
    outcome="success",
    details={
        "session_duration": 3600,
        "logout_type": "user_initiated"
    }
)
```

## Logging Authorization Events

```python
from tframex.enterprise.security.audit import log_authorization_event

# Log permission check
await log_authorization_event(
    user_id="user_123",
    action="permission_check",
    resource="agent:create",
    outcome="granted",
    details={
        "permission_source": "role:developer",
        "evaluation_time_ms": 5
    }
)

# Log access denial
await log_authorization_event(
    user_id="user_456",
    action="access_denied",
    resource="admin:delete_all",
    outcome="denied",
    details={
        "required_permission": "admin:*",
        "user_permissions": ["user:*", "agent:read"],
        "denial_reason": "insufficient_privileges"
    }
)

# Log role assignment
await log_authorization_event(
    user_id="admin_123",
    action="role_assignment",
    resource="user_456",
    outcome="success",
    details={
        "assigned_role": "developer",
        "assigned_by": "admin_123",
        "expiration": "2024-12-31T23:59:59Z"
    }
)
```

## Logging Resource Access

```python
from tframex.enterprise.security.audit import log_resource_access

# Log agent execution
await log_resource_access(
    user_id="user_123",
    resource_type="agent",
    resource_id="agent_456",
    action="execute",
    outcome="success",
    details={
        "agent_name": "DataAnalyzer",
        "execution_time_ms": 1234,
        "tokens_used": 500,
        "cost": 0.01
    }
)

# Log tool usage
await log_resource_access(
    user_id="user_123",
    resource_type="tool",
    resource_id="tool_789",
    action="execute",
    outcome="failure",
    details={
        "tool_name": "DatabaseQuery",
        "error": "Connection timeout",
        "query": "SELECT * FROM users",  # Be careful with sensitive data
        "duration_ms": 30000
    }
)

# Log data access
await log_resource_access(
    user_id="user_123",
    resource_type="data",
    resource_id="dataset_abc",
    action="read",
    outcome="success",
    details={
        "data_classification": "confidential",
        "rows_accessed": 1000,
        "fields_accessed": ["name", "email", "created_at"],
        "purpose": "analytics"
    }
)
```

## Advanced Audit Features

### Structured Audit Trails

```python
from tframex.enterprise.security.audit import AuditTrail

# Create audit trail for complex operations
audit_trail = AuditTrail(
    trail_id="trail_123",
    operation="user_data_export",
    actor_id="user_123"
)

# Log each step
async with audit_trail:
    # Step 1: Authenticate
    await audit_trail.log_step(
        "authenticate",
        outcome="success",
        details={"method": "mfa"}
    )
    
    # Step 2: Authorize
    await audit_trail.log_step(
        "authorize",
        outcome="success",
        details={"permission": "data:export"}
    )
    
    # Step 3: Execute
    try:
        data = await export_user_data(user_id)
        await audit_trail.log_step(
            "export_data",
            outcome="success",
            details={
                "records_exported": len(data),
                "format": "json"
            }
        )
    except Exception as e:
        await audit_trail.log_step(
            "export_data",
            outcome="failure",
            details={"error": str(e)}
        )
        raise

# Trail automatically closes with summary
```

### Correlation and Context

```python
from tframex.enterprise.security.audit import AuditContext

# Create correlated audit context
async with AuditContext(
    correlation_id="req_123456",
    session_id="sess_789",
    trace_id="trace_abc"
) as context:
    
    # All audit events within context are correlated
    await log_authentication_event(
        user_id="user_123",
        action="api_key_validation",
        outcome="success"
    )
    
    await log_resource_access(
        user_id="user_123",
        resource_type="agent",
        resource_id="agent_456",
        action="execute"
    )
    
    # Events automatically include correlation IDs
```

### Tamper-Proof Logging

```python
from tframex.enterprise.security.audit import TamperProofLogger

# Configure tamper-proof logging
tamper_proof_logger = TamperProofLogger(
    storage_backend=audit_storage,
    
    # Cryptographic integrity
    signing_key=os.environ["AUDIT_SIGNING_KEY"],
    hash_algorithm="sha256",
    
    # Chain events for integrity
    chain_events=True,
    
    # External verification
    external_timestamp_service="https://timestamp.example.com"
)

# Log with cryptographic proof
event = await tamper_proof_logger.log(
    event_type="critical_operation",
    details={...}
)

# Verify integrity
is_valid = await tamper_proof_logger.verify_event(event.event_id)
chain_valid = await tamper_proof_logger.verify_chain(
    start_time=datetime(2024, 1, 1),
    end_time=datetime.utcnow()
)
```

## Audit Storage Backends

### PostgreSQL Backend

```python
from tframex.enterprise.security.audit import PostgreSQLAuditStorage

audit_storage = PostgreSQLAuditStorage(
    connection_string=os.environ["DATABASE_URL"],
    
    # Table configuration
    table_name="audit_logs",
    partition_by="month",  # Partition for performance
    
    # Indexes for common queries
    indexes=[
        "actor_id",
        "event_type",
        "timestamp",
        "resource_id"
    ],
    
    # Compression for old data
    compress_after_days=30
)
```

### S3 Backend

```python
from tframex.enterprise.security.audit import S3AuditStorage

audit_storage = S3AuditStorage(
    bucket=os.environ["AUDIT_BUCKET"],
    prefix="audit-logs/",
    
    # Organization
    path_format="{year}/{month}/{day}/{hour}/",
    
    # Performance
    batch_size=100,
    flush_interval=60,  # seconds
    
    # Durability
    storage_class="GLACIER",  # For long-term retention
    server_side_encryption="AES256",
    
    # Lifecycle
    transition_to_glacier_days=30,
    expiration_days=2555  # 7 years
)
```

### Elasticsearch Backend

```python
from tframex.enterprise.security.audit import ElasticsearchAuditStorage

audit_storage = ElasticsearchAuditStorage(
    hosts=["https://es1.example.com", "https://es2.example.com"],
    
    # Index configuration
    index_prefix="tframex-audit",
    index_pattern="monthly",  # tframex-audit-2024-01
    
    # Mapping
    custom_mapping={
        "properties": {
            "actor_id": {"type": "keyword"},
            "event_type": {"type": "keyword"},
            "timestamp": {"type": "date"},
            "details": {"type": "object", "enabled": True}
        }
    },
    
    # Performance
    bulk_size=500,
    concurrent_requests=4
)
```

## Audit Queries and Analysis

### Searching Audit Logs

```python
from tframex.enterprise.security.audit import AuditQuery

# Search by user
user_events = await audit_logger.search(
    AuditQuery(
        actor_id="user_123",
        start_time=datetime.utcnow() - timedelta(days=7),
        limit=100
    )
)

# Search by event type
auth_events = await audit_logger.search(
    AuditQuery(
        event_types=[AuditEventType.AUTHENTICATION],
        outcome=AuditOutcome.FAILURE,
        start_time=datetime.utcnow() - timedelta(hours=24)
    )
)

# Complex search
complex_query = AuditQuery(
    filters={
        "actor_id": {"in": ["user_123", "user_456"]},
        "event_type": {"in": ["resource_access", "data_operation"]},
        "details.data_classification": "confidential",
        "risk_score": {"gte": 0.7}
    },
    sort_by="timestamp",
    sort_order="desc",
    limit=50
)

results = await audit_logger.search(complex_query)
```

### Audit Analytics

```python
from tframex.enterprise.security.audit import AuditAnalytics

analytics = AuditAnalytics(audit_logger)

# User activity summary
user_summary = await analytics.user_activity_summary(
    user_id="user_123",
    time_range="30d"
)
print(f"Total events: {user_summary.total_events}")
print(f"Failed authentications: {user_summary.failed_auth_count}")
print(f"Resources accessed: {user_summary.unique_resources}")

# Security metrics
security_metrics = await analytics.security_metrics(
    time_range="7d"
)
print(f"Failed login rate: {security_metrics.failed_login_rate:.2%}")
print(f"Permission denial rate: {security_metrics.permission_denial_rate:.2%}")
print(f"High risk events: {security_metrics.high_risk_event_count}")

# Anomaly detection
anomalies = await analytics.detect_anomalies(
    baseline_days=30,
    threshold_stddev=3
)
for anomaly in anomalies:
    print(f"Anomaly detected: {anomaly.description}")
    print(f"Severity: {anomaly.severity}")
    print(f"Affected users: {anomaly.affected_users}")
```

### Audit Reports

```python
from tframex.enterprise.security.audit import AuditReporter

reporter = AuditReporter(audit_logger)

# Generate compliance report
compliance_report = await reporter.generate_compliance_report(
    report_type="SOC2",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 3, 31),
    include_sections=[
        "access_control",
        "authentication",
        "data_protection",
        "incident_response"
    ]
)

# Save report
await reporter.save_report(
    compliance_report,
    format="pdf",
    output_path="/reports/soc2_q1_2024.pdf"
)

# User access report
access_report = await reporter.generate_access_report(
    user_id="user_123",
    include_details=True
)

# Security incident report
incident_report = await reporter.generate_incident_report(
    incident_id="inc_123",
    include_timeline=True,
    include_affected_resources=True
)
```

## Audit Retention and Archival

### Retention Policies

```python
from tframex.enterprise.security.audit import RetentionPolicy

# Configure retention policy
retention_policy = RetentionPolicy(
    # Default retention
    default_retention_days=90,
    
    # Event-specific retention
    event_retention={
        AuditEventType.AUTHENTICATION: 180,
        AuditEventType.AUTHORIZATION: 180,
        AuditEventType.SECURITY_INCIDENT: 2555,  # 7 years
        AuditEventType.DATA_DELETION: 2555,
        AuditEventType.CONFIGURATION_CHANGE: 365
    },
    
    # Compliance overrides
    compliance_requirements={
        "GDPR": {"min_days": 0, "max_days": 365},
        "HIPAA": {"min_days": 2190},  # 6 years
        "SOX": {"min_days": 2555}      # 7 years
    }
)

# Apply retention policy
await audit_logger.apply_retention_policy(retention_policy)
```

### Archival Process

```python
from tframex.enterprise.security.audit import AuditArchiver

archiver = AuditArchiver(
    source_storage=primary_audit_storage,
    archive_storage=s3_archive_storage
)

# Archive old logs
archive_result = await archiver.archive_logs(
    older_than_days=90,
    
    # Compression
    compress=True,
    compression_algorithm="gzip",
    
    # Encryption
    encrypt=True,
    encryption_key=os.environ["ARCHIVE_ENCRYPTION_KEY"],
    
    # Verification
    verify_archive=True,
    delete_after_verify=True
)

print(f"Archived {archive_result.events_archived} events")
print(f"Space saved: {archive_result.space_saved_mb} MB")

# Restore from archive
restore_result = await archiver.restore_logs(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    restore_to=temp_storage
)
```

## Real-Time Audit Monitoring

### Audit Streams

```python
from tframex.enterprise.security.audit import AuditStream

# Create real-time audit stream
audit_stream = AuditStream(audit_logger)

# Subscribe to events
@audit_stream.on(AuditEventType.AUTHENTICATION)
async def handle_auth_event(event):
    if event.outcome == AuditOutcome.FAILURE:
        await security_monitor.track_failed_auth(event)

@audit_stream.on(AuditEventType.SECURITY_INCIDENT)
async def handle_security_incident(event):
    await incident_response.trigger_playbook(event)
    await notify_security_team(event)

# Start streaming
await audit_stream.start()
```

### Audit Webhooks

```python
from tframex.enterprise.security.audit import AuditWebhook

# Configure webhooks for critical events
webhook = AuditWebhook(
    url="https://security.example.com/audit-webhook",
    events=[
        AuditEventType.SECURITY_INCIDENT,
        AuditEventType.PRIVILEGE_ESCALATION,
        AuditEventType.DATA_BREACH
    ],
    
    # Security
    secret_key=os.environ["WEBHOOK_SECRET"],
    
    # Reliability
    retry_attempts=3,
    retry_delay=1.0,
    
    # Batching
    batch_size=10,
    batch_timeout=5.0
)

audit_logger.add_webhook(webhook)
```

## Compliance Features

### GDPR Compliance

```python
from tframex.enterprise.security.audit import GDPRAuditCompliance

gdpr_compliance = GDPRAuditCompliance(audit_logger)

# Right to access
user_audit_data = await gdpr_compliance.export_user_audit_data(
    user_id="user_123",
    format="json"
)

# Right to erasure (with audit trail)
await gdpr_compliance.anonymize_user_audit_data(
    user_id="user_123",
    reason="user_request",
    retain_statistical_data=True
)

# Data portability
portable_data = await gdpr_compliance.export_portable_audit_data(
    user_id="user_123",
    format="machine_readable_json"
)
```

### HIPAA Compliance

```python
from tframex.enterprise.security.audit import HIPAAAuditCompliance

hipaa_compliance = HIPAAAuditCompliance(audit_logger)

# Access logs for covered entities
access_logs = await hipaa_compliance.get_phi_access_logs(
    start_date=datetime.utcnow() - timedelta(days=30),
    include_details=True
)

# Disclosure tracking
await hipaa_compliance.log_phi_disclosure(
    patient_id="patient_123",
    disclosed_to="Dr. Smith",
    purpose="treatment",
    data_disclosed=["medical_history", "lab_results"]
)
```

## Testing Audit Logging

```python
import pytest
from tframex.enterprise.testing import AuditTestHarness

@pytest.fixture
def audit_harness():
    return AuditTestHarness()

async def test_audit_logging(audit_harness):
    # Test event logging
    event = await audit_harness.log_test_event(
        event_type=AuditEventType.AUTHENTICATION,
        outcome=AuditOutcome.SUCCESS
    )
    
    # Verify event was logged
    assert await audit_harness.event_exists(event.event_id)
    
    # Verify event properties
    stored_event = await audit_harness.get_event(event.event_id)
    assert stored_event.event_type == AuditEventType.AUTHENTICATION
    assert stored_event.outcome == AuditOutcome.SUCCESS

async def test_audit_search(audit_harness):
    # Create test events
    await audit_harness.create_test_events(
        count=100,
        event_types=[AuditEventType.AUTHENTICATION, AuditEventType.RESOURCE_ACCESS]
    )
    
    # Test search
    results = await audit_harness.search(
        event_type=AuditEventType.AUTHENTICATION,
        limit=10
    )
    
    assert len(results) == 10
    assert all(e.event_type == AuditEventType.AUTHENTICATION for e in results)
```

## Best Practices

### 1. Log Appropriately

```python
# DO: Log security-relevant events
await log_authentication_event(
    user_id=user.id,
    action="login",
    outcome="success"
)

# DON'T: Log sensitive data
# Bad: logging passwords
await audit_logger.log(
    event_type="authentication",
    details={"password": user_password}  # Never do this!
)

# Good: log attempt without sensitive data
await audit_logger.log(
    event_type="authentication",
    details={"username": username, "method": "password"}
)
```

### 2. Use Structured Logging

```python
# Use consistent event structure
class AuditEventBuilder:
    @staticmethod
    def build_resource_event(user, resource, action, outcome):
        return AuditEvent(
            event_type=AuditEventType.RESOURCE_ACCESS,
            actor_id=user.id,
            resource_type=resource.__class__.__name__,
            resource_id=resource.id,
            action=action,
            outcome=outcome,
            timestamp=datetime.utcnow(),
            details={
                "resource_name": resource.name,
                "resource_owner": resource.owner_id,
                "access_level": user.access_level
            }
        )
```

### 3. Monitor Audit System Health

```python
# Monitor audit system
audit_monitor = AuditSystemMonitor(audit_logger)

# Check storage space
storage_status = await audit_monitor.check_storage()
if storage_status.usage_percent > 80:
    await alert_ops_team("Audit storage above 80%")

# Check write performance
write_perf = await audit_monitor.check_write_performance()
if write_perf.avg_latency_ms > 100:
    await alert_ops_team("Audit write latency high")

# Verify integrity
integrity_check = await audit_monitor.verify_integrity(
    last_hours=24
)
if not integrity_check.passed:
    await alert_security_team("Audit integrity check failed")
```

## Next Steps

- [Session Management](sessions) - Track user sessions
- [Security Monitoring](monitoring) - Real-time security monitoring
- [Compliance](compliance) - Meet regulatory requirements
- [Incident Response](incident-response) - Handle security incidents