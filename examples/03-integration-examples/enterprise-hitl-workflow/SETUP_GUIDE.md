# Enterprise HITL Workflow System - Setup Guide

## ✅ **Status: PRODUCTION-READY ENTERPRISE EXAMPLE**

This example demonstrates enterprise-grade Human-in-the-Loop workflows with TFrameX, featuring multi-agent AI coordination, comprehensive audit trails, and role-based approval processes.

## 🚀 **Quick Start Instructions**

### 1. **Navigate to the Example Directory**
```bash
cd /home/smirk/TFrameX/examples/03-integration-examples/enterprise-hitl-workflow
```

### 2. **Configure Environment Variables**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Llama API key
# Get your key from https://api.llama.com/
nano .env  # or use your preferred editor
```

### 3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 4. **Run the Interactive System**
```bash
python main.py
```

### 5. **Try Demo Mode (Recommended First)**
```bash
python main.py --demo
```

## 🏢 **What's Included**

✅ **Multi-Agent AI System**: 3 specialized enterprise agents  
✅ **Workflow Engine**: 4 enterprise workflow types with approval chains  
✅ **User Role System**: 7 organizational roles with permissions  
✅ **Risk Assessment**: Automated risk calculation and escalation  
✅ **Audit Logging**: Comprehensive compliance and governance trails  
✅ **Database Integration**: SQLite with enterprise schema  
✅ **Interactive Demo**: Automated scenarios + interactive mode  

## 🎯 **Available Agents**

### **WorkflowCoordinator**
- Creates and manages workflow requests
- Coordinates approval processes and notifications
- Provides status tracking and progress updates
- Ensures proper risk assessment and documentation

### **ApprovalManager**
- Processes approval requests for managers and executives
- Presents comprehensive request context and risk analysis
- Handles approvals/rejections with audit documentation
- Facilitates informed business decision-making

### **ComplianceOfficer**
- Ensures regulatory compliance and policy adherence
- Reviews workflows for risk and compliance violations
- Monitors audit trails and documentation standards
- Provides guidance on regulatory requirements

## 🔄 **Workflow Types**

### 💰 **Expense Approval**
Multi-stage approval based on expense amounts:
- **< $1,000**: Manager approval only
- **< $10,000**: Manager → Director approval
- **< $50,000**: Manager → Director → Executive approval
- **≥ $50,000**: Full chain + Compliance review

### 🖥️ **Infrastructure Change**
IT system modification approval based on impact:
- **Low Impact**: IT Admin approval
- **Medium Impact**: IT Admin → Security approval
- **High Impact**: IT Admin → Security → Director approval
- **Critical Impact**: Full approval chain with Executive oversight

### 📄 **Contract Approval**
Legal contract review based on financial value:
- **< $50,000**: Manager approval
- **< $500,000**: Manager → Compliance approval
- **< $2,000,000**: Manager → Compliance → Director approval
- **≥ $2,000,000**: Full approval chain

### 🎧 **Customer Escalation**
Customer service issue escalation based on severity:
- **Minor Issues**: Manager approval
- **Moderate Issues**: Manager → Director approval
- **Major Issues**: Manager → Director approval
- **Critical Issues**: Manager → Director → Executive approval

## 👥 **Simulated Enterprise Users**

The system includes 7 simulated users representing different organizational roles:

| User ID | Name | Role | Permissions |
|---------|------|------|-------------|
| john.doe | John Doe | Employee | Create requests |
| sarah.manager | Sarah Johnson | Manager | Approve low-risk, first-stage |
| mike.director | Mike Chen | Director | Approve medium-high risk |
| lisa.executive | Lisa Williams | Executive | Approve critical requests |
| bob.compliance | Bob Anderson | Compliance | Financial/contract review |
| alice.security | Alice Brown | Security | IT security review |
| tom.itadmin | Tom Davis | IT Admin | Technical approvals |

## 💡 **Example Commands**

### **Creating Workflow Requests**
```
"Create an expense approval request for $5,000 travel costs for Q4 conference"

"Create an infrastructure change request for database migration with high impact"

"Create a contract approval workflow for a $750,000 software licensing agreement"

"Create a customer escalation for a critical billing system outage affecting 1000+ customers"
```

### **Processing Approvals**
```
"Show me pending approvals for sarah.manager"

"Approve workflow WF-1234567890-1234 with comment 'Approved for strategic value'"

"Reject workflow WF-1234567890-5678 due to insufficient business justification"
```

### **Status and Monitoring**
```
"Check the status of workflow WF-1234567890-1234"

"Show me the complete audit trail for workflow WF-1234567890-1234"

"List all workflows created by john.doe in the last week"
```

### **Compliance and Risk**
```
"Review all high-risk workflows for compliance violations"

"Show me workflows that require compliance review"

"Generate an audit report for all expense approvals this quarter"
```

## 🧪 **Demo Scenarios**

The automated demo (`python main.py --demo`) runs these scenarios:

### **Scenario 1: High-Value Expense Request**
- Creates a $15,000 executive travel expense request
- Demonstrates multi-stage approval chain (Manager → Director → Executive)
- Shows risk assessment and appropriate escalation

### **Scenario 2: Manager Approval Queue**
- Displays pending approvals for a manager role
- Shows how different workflow types appear in approval queues
- Demonstrates role-based filtering

### **Scenario 3: Infrastructure Change Request**
- Creates a high-impact database migration request
- Shows IT-specific approval chain (IT Admin → Security → Director)
- Demonstrates technical workflow handling

### **Scenario 4: Compliance Review**
- Compliance officer reviews recent infrastructure changes
- Shows compliance-specific tools and perspectives
- Demonstrates regulatory oversight capabilities

## 📊 **Database Schema**

The system creates 3 tables in `enterprise_workflows.db`:

### **workflows**
```sql
- id (TEXT PRIMARY KEY)           -- Unique workflow identifier
- type (TEXT)                     -- Workflow type (expense_approval, etc.)
- title (TEXT)                    -- Human-readable title
- description (TEXT)              -- Detailed description
- requester (TEXT)                -- User who created the request
- requester_role (TEXT)           -- Organizational role of requester
- data (TEXT)                     -- JSON workflow data
- risk_level (TEXT)               -- Assessed risk level
- required_approvers (TEXT)       -- JSON array of required approver roles
- created_at (TEXT)               -- ISO timestamp
- status (TEXT)                   -- Current workflow status
- current_stage (INTEGER)         -- Current approval stage
- approvals (TEXT)                -- JSON array of approvals
- comments (TEXT)                 -- JSON array of comments
```

### **audit_log**
```sql
- id (INTEGER PRIMARY KEY)        -- Auto-increment log entry ID
- workflow_id (TEXT)              -- Reference to workflow
- user_id (TEXT)                  -- User performing action
- action (TEXT)                   -- Action performed
- details (TEXT)                  -- Detailed action description
- timestamp (TEXT)                -- ISO timestamp
- ip_address (TEXT)               -- User IP address
- user_agent (TEXT)               -- User agent string
```

### **notifications**
```sql
- id (INTEGER PRIMARY KEY)        -- Auto-increment notification ID
- recipient (TEXT)                -- User to notify
- title (TEXT)                    -- Notification title
- message (TEXT)                  -- Notification content
- workflow_id (TEXT)              -- Related workflow (optional)
- created_at (TEXT)               -- ISO timestamp
- read_at (TEXT)                  -- Read timestamp (nullable)
- priority (TEXT)                 -- Notification priority
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# LLM Configuration
LLAMA_API_KEY=your_llama_api_key_here
LLAMA_BASE_URL=https://api.llama.com/compat/v1/
LLAMA_MODEL=Llama-4-Maverick-17B-128E-Instruct-FP8

# Risk Thresholds
LOW_RISK_EXPENSE_THRESHOLD=1000
MEDIUM_RISK_EXPENSE_THRESHOLD=10000
HIGH_RISK_EXPENSE_THRESHOLD=50000

# Enterprise Settings
COMPANY_NAME="TFrameX Enterprises"
ENVIRONMENT=development
```

### **Workflow Type Configuration**
Approval chains are defined in `main.py` and can be customized:

```python
workflow_configs = {
    "expense_approval": {
        "approval_chain": {
            RiskLevel.LOW: [UserRole.MANAGER],
            RiskLevel.MEDIUM: [UserRole.MANAGER, UserRole.DIRECTOR],
            RiskLevel.HIGH: [UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EXECUTIVE],
            RiskLevel.CRITICAL: [UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EXECUTIVE, UserRole.COMPLIANCE]
        }
    }
}
```

## 🚨 **Troubleshooting**

### **Database Issues**
If you encounter database errors:
```bash
# Remove existing database to reset
rm enterprise_workflows.db

# Restart the application
python main.py
```

### **Permission Errors**
If workflows aren't approved:
- Verify the user has the correct role for the approval stage
- Check that the workflow is in "awaiting_approval" status
- Ensure the user is authorized for the current approval stage

### **AI Agent Issues**
If agents don't respond properly:
- Check API key configuration in `.env`
- Verify network connectivity to Llama API
- Review logs for tool calling issues
- Ensure `parse_text_tool_calls=True` is set

### **Workflow Creation Failures**
If workflow creation fails:
- Verify all required fields are provided
- Check that the workflow type is supported
- Ensure the requester user exists in the system
- Review data format for workflow-specific requirements

## 📈 **Production Deployment**

### **Security Considerations**
- **API Keys**: Store in secure environment variables or key management
- **Database**: Use PostgreSQL or MySQL for production
- **Authentication**: Integrate with enterprise identity providers
- **Encryption**: Enable TLS for all communications

### **Scalability**
- **Database**: Configure connection pooling and read replicas
- **Caching**: Add Redis for session and workflow state caching
- **Load Balancing**: Deploy multiple application instances
- **Monitoring**: Add APM and logging aggregation

### **Integration**
- **SSO**: Integrate with SAML/OAuth identity providers
- **Notifications**: Connect to enterprise email/messaging systems
- **ERP Integration**: Connect to SAP, Oracle, or other enterprise systems
- **Reporting**: Export to enterprise BI and analytics platforms

## 🎓 **Learning Objectives**

This example demonstrates:

1. **Enterprise AI Architecture**: Building AI systems for regulated environments
2. **Human-AI Collaboration**: Combining AI efficiency with human judgment
3. **Workflow Orchestration**: Complex multi-stage business process automation
4. **Compliance by Design**: Built-in audit trails and regulatory compliance
5. **Role-Based Security**: Enterprise-grade access control implementation
6. **Risk Management**: Automated risk assessment with appropriate escalation
7. **Multi-Agent Coordination**: Specialized AI agents working together
8. **Production Patterns**: Scalable, secure, and maintainable enterprise AI

## 🔗 **Next Steps**

### **Extend the System**
- Add new workflow types (hiring, procurement, etc.)
- Implement email/SMS notifications
- Create management dashboards
- Add workflow templates and automation rules

### **Enterprise Integration**
- Connect to existing ERP/HR systems
- Implement SSO authentication
- Add compliance reporting features
- Create mobile approval interfaces

### **Advanced Features**
- Machine learning for risk prediction
- Natural language workflow creation
- Advanced analytics and reporting
- Integration with external approval systems

---

**🏢 Ready to deploy enterprise-grade AI workflows with human oversight!**

**🔗 For more TFrameX examples:**
- AWS Documentation MCP: `../aws-documentation-mcp/`
- Basic MCP Integration: `../mcp-integration/`
- Web Chatbot: `../web-chatbot/`