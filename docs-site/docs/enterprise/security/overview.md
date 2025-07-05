---
sidebar_position: 1
title: Security Overview
---

# Enterprise Security Overview

TFrameX Enterprise provides comprehensive security features to protect your AI agent deployments, ensure compliance, and maintain audit trails.

## Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Client Request                     │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│              Security Middleware                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │Authentication│  │Authorization │  │   Audit   │ │
│  │   Provider   │  │    (RBAC)    │  │  Logger   │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                  TFrameX Core                        │
│         Agents, Tools, Flows, Memory                 │
└─────────────────────────────────────────────────────┘
```

## Key Security Features

### 🔐 Authentication
Multiple authentication providers to integrate with your existing infrastructure:
- **JWT** - JSON Web Tokens for stateless authentication
- **OAuth2** - Integration with OAuth2 providers
- **API Keys** - Simple key-based authentication
- **Basic Auth** - Username/password authentication

### 🛡️ Authorization (RBAC)
Fine-grained access control with:
- **Hierarchical Roles** - Role inheritance and composition
- **Resource Permissions** - Control access to agents, tools, flows
- **Dynamic Policies** - Time-based and context-aware access
- **Permission Caching** - High-performance authorization

### 📋 Audit Logging
Comprehensive audit trail for compliance:
- **All Actions Logged** - Authentication, authorization, execution
- **Tamper-Proof Storage** - Cryptographic integrity
- **Flexible Retention** - Configure retention policies
- **Search and Export** - Query and export audit logs

### 🔒 Session Management
Secure session handling with:
- **Multiple Backends** - Memory, Redis, Database
- **Session Security** - Encryption, timeout, refresh
- **Concurrent Sessions** - Control multi-device access
- **Session Revocation** - Immediate session termination

## Quick Start Security Setup

### 1. Basic Authentication

```python
from tframex.enterprise import EnterpriseApp

# Configure with API key authentication
config = {
    "enterprise": {
        "enabled": True,
        "security": {
            "authentication": {
                "providers": [{
                    "type": "api_key",
                    "header_name": "X-API-Key"
                }]
            }
        }
    }
}

app = EnterpriseApp(enterprise_config=config)
```

### 2. JWT Authentication with RBAC

```python
config = {
    "enterprise": {
        "security": {
            "authentication": {
                "providers": [{
                    "type": "jwt",
                    "secret_key": "your-secret-key",
                    "algorithm": "HS256"
                }]
            },
            "rbac": {
                "enabled": True,
                "roles": [
                    {
                        "name": "admin",
                        "permissions": ["*"]
                    },
                    {
                        "name": "user",
                        "permissions": ["agent:read", "agent:execute"]
                    }
                ]
            }
        }
    }
}
```

### 3. Full Security Stack

```python
from tframex.enterprise import create_enhanced_enterprise_app

app = create_enhanced_enterprise_app(
    config_path="security_config.yaml",
    enable_audit=True,
    enable_session_management=True,
    enable_rbac=True
)

# Secure endpoint example
@app.route("/execute-agent")
@require_authentication
@require_permission("agent:execute")
@audit_log
async def execute_agent(request, user):
    agent_name = request.json["agent"]
    prompt = request.json["prompt"]
    
    async with app.run_context(user=user) as rt:
        result = await rt.call_agent(agent_name, prompt)
        return {"result": result}
```

## Security Patterns

### API Gateway Pattern

```python
from tframex.enterprise.security import SecurityGateway

gateway = SecurityGateway(
    authentication_providers=["jwt", "api_key"],
    rate_limiting=True,
    ip_whitelist=["10.0.0.0/8"],
    cors_origins=["https://app.example.com"]
)

@gateway.protected
async def secure_endpoint(request, user):
    # User is authenticated and authorized
    return {"user": user.username}
```

### Multi-Tenant Security

```python
from tframex.enterprise.security import TenantIsolation

# Configure tenant isolation
tenant_config = {
    "isolation_level": "strict",
    "data_separation": "logical",  # or "physical"
    "tenant_id_header": "X-Tenant-ID"
}

app = EnterpriseApp(
    enterprise_config=config,
    tenant_isolation=tenant_config
)

# Agents are automatically scoped to tenant
async with app.run_context(tenant_id="tenant-123") as rt:
    # Only accesses tenant-123 data
    result = await rt.call_agent("Assistant", "Show my data")
```

### Zero Trust Architecture

```python
from tframex.enterprise.security import ZeroTrustPolicy

policy = ZeroTrustPolicy(
    verify_every_request=True,
    require_mfa=True,
    encrypt_all_data=True,
    network_segmentation=True
)

app = EnterpriseApp(
    enterprise_config=config,
    security_policy=policy
)
```

## Security Best Practices

### 1. Defense in Depth

Implement multiple layers of security:

```python
# Layer 1: Network security (handled by infrastructure)
# Layer 2: Authentication
# Layer 3: Authorization
# Layer 4: Input validation
# Layer 5: Audit logging

from tframex.enterprise.security import DefenseInDepth

security = DefenseInDepth(
    layers=[
        AuthenticationLayer(providers=["jwt", "mfa"]),
        AuthorizationLayer(rbac_enabled=True),
        ValidationLayer(strict_mode=True),
        AuditLayer(log_everything=True)
    ]
)
```

### 2. Principle of Least Privilege

```python
# Define minimal permissions for each role
roles = [
    {
        "name": "agent_operator",
        "permissions": [
            "agent:read",
            "agent:execute",
            "tool:read"
        ]
        # No create, update, or delete permissions
    },
    {
        "name": "developer",
        "permissions": [
            "agent:*",
            "tool:*",
            "flow:read",
            "flow:execute"
        ]
        # No admin permissions
    }
]
```

### 3. Secure Configuration

```python
# Use environment variables for secrets
import os
from tframex.enterprise.security import SecureConfig

config = SecureConfig(
    jwt_secret=os.environ["JWT_SECRET"],
    encryption_key=os.environ["ENCRYPTION_KEY"],
    validate_env_vars=True
)

# Validate configuration at startup
config.validate_security_settings()
```

### 4. Regular Security Audits

```python
from tframex.enterprise.security import SecurityAuditor

auditor = SecurityAuditor(app)

# Run security checks
report = await auditor.run_audit(
    check_permissions=True,
    check_encryption=True,
    check_vulnerabilities=True,
    check_compliance=True
)

# Review and act on findings
for issue in report.issues:
    print(f"Security issue: {issue.severity} - {issue.description}")
```

## Compliance Features

### GDPR Compliance

```python
from tframex.enterprise.security import GDPRCompliance

gdpr = GDPRCompliance(
    data_retention_days=365,
    enable_right_to_deletion=True,
    enable_data_portability=True,
    anonymize_logs=True
)

app = EnterpriseApp(
    enterprise_config=config,
    compliance_policies=[gdpr]
)
```

### HIPAA Compliance

```python
from tframex.enterprise.security import HIPAACompliance

hipaa = HIPAACompliance(
    encrypt_data_at_rest=True,
    encrypt_data_in_transit=True,
    audit_all_access=True,
    access_control_required=True
)
```

### SOC 2 Compliance

```python
from tframex.enterprise.security import SOC2Compliance

soc2 = SOC2Compliance(
    security_monitoring=True,
    availability_monitoring=True,
    processing_integrity=True,
    confidentiality_controls=True
)
```

## Security Monitoring

### Real-Time Threat Detection

```python
from tframex.enterprise.security import ThreatDetection

detector = ThreatDetection(
    anomaly_detection=True,
    brute_force_protection=True,
    sql_injection_detection=True,
    rate_limit_violations=True
)

@detector.monitor
async def protected_operation():
    # Automatically monitored for threats
    pass
```

### Security Metrics

```python
# Track security metrics
security_metrics = app.get_security_metrics()

print(f"Failed login attempts: {security_metrics.failed_logins}")
print(f"Permission denials: {security_metrics.permission_denials}")
print(f"Active sessions: {security_metrics.active_sessions}")
print(f"Audit events: {security_metrics.audit_events}")
```

## Incident Response

### Automated Response

```python
from tframex.enterprise.security import IncidentResponse

incident_response = IncidentResponse(
    auto_block_ips=True,
    auto_revoke_tokens=True,
    notify_security_team=True,
    create_incident_report=True
)

# Define response rules
incident_response.add_rule(
    condition="failed_logins > 5",
    action="block_ip",
    duration=3600
)

incident_response.add_rule(
    condition="suspicious_activity",
    action="alert_security_team",
    priority="high"
)
```

### Security Playbooks

```python
from tframex.enterprise.security import SecurityPlaybook

# Define playbook for data breach
data_breach_playbook = SecurityPlaybook(
    name="data_breach_response",
    steps=[
        "isolate_affected_systems",
        "revoke_all_tokens",
        "notify_security_team",
        "create_forensic_snapshot",
        "begin_investigation",
        "notify_affected_users",
        "file_compliance_report"
    ]
)

# Execute playbook
await incident_response.execute_playbook(data_breach_playbook)
```

## Next Steps

1. **[Authentication](authentication)** - Set up authentication providers
2. **[Authorization](authorization)** - Configure RBAC and permissions
3. **[Audit Logging](audit)** - Implement compliance logging
4. **[Session Management](sessions)** - Configure secure sessions
5. **[Security Hardening](hardening)** - Additional security measures

## Security Checklist

- [ ] Enable authentication for all endpoints
- [ ] Configure RBAC with least privilege
- [ ] Enable audit logging
- [ ] Use HTTPS/TLS for all connections
- [ ] Encrypt sensitive data at rest
- [ ] Implement rate limiting
- [ ] Regular security audits
- [ ] Incident response plan
- [ ] Security training for team
- [ ] Regular security updates