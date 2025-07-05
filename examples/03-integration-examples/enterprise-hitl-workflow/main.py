#!/usr/bin/env python3
"""
Enterprise Human-in-the-Loop (HITL) Workflow System
===================================================

This example demonstrates how enterprises can use TFrameX to build sophisticated 
AI-assisted workflows with mandatory human oversight, approval processes, and 
comprehensive audit trails.

Use Cases:
- Financial transaction processing with compliance reviews
- Document approval workflows with legal oversight
- Customer service escalation with supervisor approval
- IT infrastructure changes with security review
- Strategic business decisions with executive approval

Features:
- Multi-stage approval workflows
- Role-based access control
- Comprehensive audit logging
- Risk assessment and compliance
- Real-time notifications
- Enterprise integration patterns
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from dotenv import load_dotenv
from tframex import TFrameXApp, OpenAIChatLLM, Message
from tframex.util.logging import setup_logging

# Load environment variables
load_dotenv()

# Configure logging
setup_logging(level=logging.INFO)
logger = logging.getLogger("enterprise_hitl")

# Configure component logging
logging.getLogger("tframex.app").setLevel(logging.INFO)
logging.getLogger("tframex.agents").setLevel(logging.INFO)
logging.getLogger("tframex.util.llms").setLevel(logging.WARNING)

class WorkflowStatus(Enum):
    """Workflow execution status."""
    INITIATED = "initiated"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    FAILED = "failed"

class UserRole(Enum):
    """User roles in the enterprise system."""
    EMPLOYEE = "employee"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    IT_ADMIN = "it_admin"

class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class WorkflowRequest:
    """Enterprise workflow request."""
    id: str
    type: str
    title: str
    description: str
    requester: str
    requester_role: UserRole
    data: Dict[str, Any]
    risk_level: RiskLevel
    required_approvers: List[UserRole]
    created_at: datetime
    status: WorkflowStatus
    current_stage: int = 0
    approvals: List[Dict[str, Any]] = None
    comments: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.approvals is None:
            self.approvals = []
        if self.comments is None:
            self.comments = []

class EnterpriseWorkflowSystem:
    """Enterprise-grade Human-in-the-Loop workflow system."""
    
    def __init__(self):
        """Initialize the enterprise workflow system."""
        self.app = None
        self.llm = self._setup_llm()
        self.db_path = "enterprise_workflows.db"
        self._init_database()
        
        # Simulated enterprise users
        self.users = {
            "john.doe": {"name": "John Doe", "role": UserRole.EMPLOYEE, "email": "john.doe@company.com"},
            "sarah.manager": {"name": "Sarah Johnson", "role": UserRole.MANAGER, "email": "sarah.johnson@company.com"},
            "mike.director": {"name": "Mike Chen", "role": UserRole.DIRECTOR, "email": "mike.chen@company.com"},
            "lisa.executive": {"name": "Lisa Williams", "role": UserRole.EXECUTIVE, "email": "lisa.williams@company.com"},
            "bob.compliance": {"name": "Bob Anderson", "role": UserRole.COMPLIANCE, "email": "bob.anderson@company.com"},
            "alice.security": {"name": "Alice Brown", "role": UserRole.SECURITY, "email": "alice.brown@company.com"},
            "tom.itadmin": {"name": "Tom Davis", "role": UserRole.IT_ADMIN, "email": "tom.davis@company.com"}
        }
        
        # Workflow type configurations
        self.workflow_configs = {
            "expense_approval": {
                "name": "Expense Approval",
                "description": "Employee expense reimbursement requests",
                "approval_chain": {
                    RiskLevel.LOW: [UserRole.MANAGER],
                    RiskLevel.MEDIUM: [UserRole.MANAGER, UserRole.DIRECTOR],
                    RiskLevel.HIGH: [UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EXECUTIVE],
                    RiskLevel.CRITICAL: [UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EXECUTIVE, UserRole.COMPLIANCE]
                }
            },
            "infrastructure_change": {
                "name": "Infrastructure Change",
                "description": "IT infrastructure modification requests",
                "approval_chain": {
                    RiskLevel.LOW: [UserRole.IT_ADMIN],
                    RiskLevel.MEDIUM: [UserRole.IT_ADMIN, UserRole.SECURITY],
                    RiskLevel.HIGH: [UserRole.IT_ADMIN, UserRole.SECURITY, UserRole.DIRECTOR],
                    RiskLevel.CRITICAL: [UserRole.IT_ADMIN, UserRole.SECURITY, UserRole.DIRECTOR, UserRole.EXECUTIVE]
                }
            },
            "contract_approval": {
                "name": "Contract Approval",
                "description": "Legal contract and agreement approvals",
                "approval_chain": {
                    RiskLevel.LOW: [UserRole.MANAGER],
                    RiskLevel.MEDIUM: [UserRole.MANAGER, UserRole.COMPLIANCE],
                    RiskLevel.HIGH: [UserRole.MANAGER, UserRole.COMPLIANCE, UserRole.DIRECTOR],
                    RiskLevel.CRITICAL: [UserRole.MANAGER, UserRole.COMPLIANCE, UserRole.DIRECTOR, UserRole.EXECUTIVE]
                }
            },
            "customer_escalation": {
                "name": "Customer Service Escalation",
                "description": "Customer service issue escalation workflow",
                "approval_chain": {
                    RiskLevel.LOW: [UserRole.MANAGER],
                    RiskLevel.MEDIUM: [UserRole.MANAGER, UserRole.DIRECTOR],
                    RiskLevel.HIGH: [UserRole.MANAGER, UserRole.DIRECTOR],
                    RiskLevel.CRITICAL: [UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EXECUTIVE]
                }
            }
        }
        
    def _setup_llm(self) -> OpenAIChatLLM:
        """Set up the LLM with credentials from environment variables."""
        api_key = os.getenv("LLAMA_API_KEY")
        if not api_key:
            raise ValueError("LLAMA_API_KEY environment variable is required")
            
        return OpenAIChatLLM(
            model_name=os.getenv("LLAMA_MODEL", "Llama-4-Maverick-17B-128E-Instruct-FP8"),
            api_base_url=os.getenv("LLAMA_BASE_URL", "https://api.llama.com/compat/v1/"),
            api_key=api_key,
            parse_text_tool_calls=True
        )
    
    def _init_database(self):
        """Initialize the enterprise workflow database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Workflows table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                requester TEXT NOT NULL,
                requester_role TEXT NOT NULL,
                data TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                required_approvers TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                current_stage INTEGER NOT NULL,
                approvals TEXT NOT NULL,
                comments TEXT NOT NULL
            )
        """)
        
        # Audit log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT
            )
        """)
        
        # Notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                workflow_id TEXT,
                created_at TEXT NOT NULL,
                read_at TEXT,
                priority TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        
    def _setup_app(self) -> TFrameXApp:
        """Set up TFrameX application with enterprise agents."""
        app = TFrameXApp(
            default_llm=self.llm,
            enable_mcp_roots=False,
            enable_mcp_sampling=False
        )
        
        # Register enterprise tools
        self._register_enterprise_tools(app)
        
        # Register specialized agents
        self._register_enterprise_agents(app)
        
        return app
    
    def _register_enterprise_tools(self, app: TFrameXApp):
        """Register enterprise workflow tools."""
        
        @app.tool(
            name="create_workflow_request",
            description="Create a new enterprise workflow request"
        )
        async def create_workflow_request(
            workflow_type: str,
            title: str,
            description: str,
            requester: str,
            request_data: str
        ) -> str:
            """Create a new workflow request."""
            try:
                # Handle potential JSON parsing issues from text-based tool calls
                if isinstance(request_data, str):
                    # Clean up common formatting issues
                    request_data = request_data.replace('\\"', '"').replace("\\\\", "\\")
                    # Try to parse as JSON
                    try:
                        data = json.loads(request_data)
                    except json.JSONDecodeError:
                        # If JSON parsing fails, try to create a simple data structure
                        logger.warning(f"Failed to parse JSON: {request_data}, creating default structure")
                        data = {"description": request_data}
                else:
                    data = request_data
                
                request_id = await self.create_workflow_request(
                    workflow_type, title, description, requester, data
                )
                return f"✅ Workflow request created successfully. ID: {request_id}"
            except Exception as e:
                logger.error(f"Failed to create workflow request: {e}")
                return f"❌ Failed to create workflow request: {str(e)}"
        
        @app.tool(
            name="get_pending_approvals",
            description="Get pending approval requests for a user"
        )
        async def get_pending_approvals(user_id: str) -> str:
            """Get pending approvals for a user."""
            try:
                pending = await self.get_pending_approvals(user_id)
                if not pending:
                    return "📋 No pending approvals found."
                
                result = "📋 **Pending Approvals:**\n\n"
                for workflow in pending:
                    result += f"**{workflow['title']}** (ID: {workflow['id']})\n"
                    result += f"  • Type: {workflow['type']}\n"
                    result += f"  • Requester: {workflow['requester']}\n"
                    result += f"  • Risk Level: {workflow['risk_level']}\n"
                    result += f"  • Created: {workflow['created_at']}\n\n"
                
                return result
            except Exception as e:
                logger.error(f"Failed to get pending approvals: {e}")
                return f"❌ Failed to get pending approvals: {str(e)}"
        
        @app.tool(
            name="approve_workflow",
            description="Approve a workflow request"
        )
        async def approve_workflow(workflow_id: str, approver: str, comments: str = "") -> str:
            """Approve a workflow request."""
            try:
                success = await self.approve_workflow(workflow_id, approver, comments)
                if success:
                    return f"✅ Workflow {workflow_id} approved successfully."
                else:
                    return f"❌ Failed to approve workflow {workflow_id}. Check permissions and workflow status."
            except Exception as e:
                logger.error(f"Failed to approve workflow: {e}")
                return f"❌ Failed to approve workflow: {str(e)}"
        
        @app.tool(
            name="reject_workflow",
            description="Reject a workflow request"
        )
        async def reject_workflow(workflow_id: str, rejector: str, reason: str) -> str:
            """Reject a workflow request."""
            try:
                success = await self.reject_workflow(workflow_id, rejector, reason)
                if success:
                    return f"✅ Workflow {workflow_id} rejected."
                else:
                    return f"❌ Failed to reject workflow {workflow_id}. Check permissions and workflow status."
            except Exception as e:
                logger.error(f"Failed to reject workflow: {e}")
                return f"❌ Failed to reject workflow: {str(e)}"
        
        @app.tool(
            name="get_workflow_status",
            description="Get the current status of a workflow"
        )
        async def get_workflow_status(workflow_id: str) -> str:
            """Get workflow status and details."""
            try:
                workflow = await self.get_workflow(workflow_id)
                if not workflow:
                    return f"❌ Workflow {workflow_id} not found."
                
                result = f"📊 **Workflow Status: {workflow['title']}**\n\n"
                result += f"• **ID:** {workflow['id']}\n"
                result += f"• **Type:** {workflow['type']}\n"
                result += f"• **Status:** {workflow['status']}\n"
                result += f"• **Risk Level:** {workflow['risk_level']}\n"
                result += f"• **Requester:** {workflow['requester']}\n"
                result += f"• **Created:** {workflow['created_at']}\n"
                result += f"• **Current Stage:** {workflow['current_stage']}\n\n"
                
                if workflow['approvals']:
                    result += "**Approvals:**\n"
                    for approval in workflow['approvals']:
                        result += f"  ✅ {approval['approver']} - {approval['timestamp']}\n"
                        if approval.get('comments'):
                            result += f"     💬 \"{approval['comments']}\"\n"
                
                return result
            except Exception as e:
                logger.error(f"Failed to get workflow status: {e}")
                return f"❌ Failed to get workflow status: {str(e)}"
        
        @app.tool(
            name="get_audit_trail",
            description="Get the audit trail for a workflow"
        )
        async def get_audit_trail(workflow_id: str) -> str:
            """Get the complete audit trail for a workflow."""
            try:
                trail = await self.get_audit_trail(workflow_id)
                if not trail:
                    return f"📋 No audit trail found for workflow {workflow_id}."
                
                result = f"📋 **Audit Trail for Workflow {workflow_id}:**\n\n"
                for entry in trail:
                    result += f"• **{entry['timestamp']}** - {entry['user_id']}\n"
                    result += f"  Action: {entry['action']}\n"
                    result += f"  Details: {entry['details']}\n\n"
                
                return result
            except Exception as e:
                logger.error(f"Failed to get audit trail: {e}")
                return f"❌ Failed to get audit trail: {str(e)}"
    
    def _register_enterprise_agents(self, app: TFrameXApp):
        """Register specialized enterprise agents."""
        
        @app.agent(
            name="WorkflowCoordinator",
            description="Coordinates enterprise workflows and human approvals",
            system_prompt="""You are an Enterprise Workflow Coordinator AI assistant. You help manage complex business processes that require human oversight and approval.

Your responsibilities:
1. Help users create workflow requests with proper documentation
2. Coordinate approval processes and notify appropriate stakeholders
3. Provide status updates and track workflow progress
4. Ensure compliance with enterprise policies
5. Facilitate communication between requesters and approvers

Key principles:
- Always maintain audit trails for compliance
- Respect role-based access controls
- Escalate high-risk requests appropriately
- Provide clear status updates and next steps
- Help users understand approval requirements

Available tools: {available_tools_descriptions}

When users need to create workflows, gather all necessary information first, then create the request with appropriate risk assessment.""",
            tools=[
                "create_workflow_request",
                "get_pending_approvals", 
                "get_workflow_status",
                "get_audit_trail"
            ],
            strip_think_tags=True
        )
        async def workflow_coordinator():
            """Enterprise workflow coordination agent."""
            pass
        
        @app.agent(
            name="ApprovalManager", 
            description="Manages approval processes and decision making",
            system_prompt="""You are an Enterprise Approval Manager AI assistant. You help managers, directors, and executives efficiently review and process approval requests.

Your responsibilities:
1. Present approval requests with all relevant context
2. Highlight risk factors and compliance considerations
3. Facilitate informed decision-making
4. Process approvals and rejections with proper documentation
5. Escalate when appropriate based on policies

Key principles:
- Provide comprehensive request summaries
- Highlight potential risks and impacts
- Ensure proper justification for decisions
- Maintain audit compliance
- Respect organizational hierarchy

Available tools: {available_tools_descriptions}

When presenting approval requests, always include risk assessment, business justification, and potential impacts. Help approvers make informed decisions efficiently.""",
            tools=[
                "get_pending_approvals",
                "approve_workflow",
                "reject_workflow",
                "get_workflow_status",
                "get_audit_trail"
            ],
            strip_think_tags=True
        )
        async def approval_manager():
            """Enterprise approval management agent."""
            pass
        
        @app.agent(
            name="ComplianceOfficer",
            description="Ensures regulatory compliance and risk management",
            system_prompt="""You are an Enterprise Compliance Officer AI assistant. You ensure all workflows meet regulatory requirements and organizational policies.

Your responsibilities:
1. Review workflows for compliance and regulatory requirements
2. Assess risk levels and recommend appropriate controls
3. Monitor audit trails and documentation standards
4. Flag potential compliance violations
5. Provide guidance on regulatory requirements

Key principles:
- Prioritize compliance and risk management
- Ensure complete documentation and audit trails
- Escalate high-risk or non-compliant requests
- Provide clear guidance on requirements
- Monitor for policy violations

Available tools: {available_tools_descriptions}

Focus on risk assessment, compliance verification, and ensuring proper documentation. Always consider regulatory implications and organizational policies.""",
            tools=[
                "get_workflow_status",
                "get_audit_trail",
                "get_pending_approvals",
                "approve_workflow",
                "reject_workflow"
            ],
            strip_think_tags=True
        )
        async def compliance_officer():
            """Enterprise compliance management agent."""
            pass
    
    async def create_workflow_request(
        self, 
        workflow_type: str,
        title: str,
        description: str,
        requester: str,
        data: Dict[str, Any]
    ) -> str:
        """Create a new workflow request."""
        # Generate unique workflow ID
        workflow_id = f"WF-{int(time.time())}-{hash(title) % 10000:04d}"
        
        # Get requester info
        if requester not in self.users:
            raise ValueError(f"Unknown user: {requester}")
        
        requester_info = self.users[requester]
        requester_role = requester_info["role"]
        
        # Assess risk level based on workflow type and data
        risk_level = self._assess_risk_level(workflow_type, data)
        
        # Determine required approvers
        config = self.workflow_configs.get(workflow_type)
        if not config:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        required_approvers = config["approval_chain"][risk_level]
        
        # Create workflow request
        workflow = WorkflowRequest(
            id=workflow_id,
            type=workflow_type,
            title=title,
            description=description,
            requester=requester,
            requester_role=requester_role,
            data=data,
            risk_level=risk_level,
            required_approvers=required_approvers,
            created_at=datetime.now(),
            status=WorkflowStatus.AWAITING_APPROVAL
        )
        
        # Save to database
        await self._save_workflow(workflow)
        
        # Log audit entry
        await self._log_audit(
            workflow_id,
            requester,
            "WORKFLOW_CREATED",
            f"Created {workflow_type} workflow: {title}"
        )
        
        # Send notifications to approvers
        await self._notify_approvers(workflow)
        
        logger.info(f"Created workflow {workflow_id}: {title} (Risk: {risk_level.value})")
        return workflow_id
    
    def _assess_risk_level(self, workflow_type: str, data: Dict[str, Any]) -> RiskLevel:
        """Assess risk level based on workflow type and data."""
        if workflow_type == "expense_approval":
            amount = data.get("amount", 0)
            if amount < 1000:
                return RiskLevel.LOW
            elif amount < 10000:
                return RiskLevel.MEDIUM
            elif amount < 50000:
                return RiskLevel.HIGH
            else:
                return RiskLevel.CRITICAL
                
        elif workflow_type == "infrastructure_change":
            impact = data.get("impact", "low")
            if impact == "low":
                return RiskLevel.LOW
            elif impact == "medium":
                return RiskLevel.MEDIUM
            elif impact == "high":
                return RiskLevel.HIGH
            else:
                return RiskLevel.CRITICAL
                
        elif workflow_type == "contract_approval":
            value = data.get("contract_value", 0)
            if value < 50000:
                return RiskLevel.LOW
            elif value < 500000:
                return RiskLevel.MEDIUM
            elif value < 2000000:
                return RiskLevel.HIGH
            else:
                return RiskLevel.CRITICAL
                
        elif workflow_type == "customer_escalation":
            severity = data.get("severity", "low")
            if severity == "low":
                return RiskLevel.LOW
            elif severity == "medium":
                return RiskLevel.MEDIUM
            elif severity == "high":
                return RiskLevel.HIGH
            else:
                return RiskLevel.CRITICAL
        
        # Default to medium risk
        return RiskLevel.MEDIUM
    
    async def _save_workflow(self, workflow: WorkflowRequest):
        """Save workflow to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO workflows (
                id, type, title, description, requester, requester_role,
                data, risk_level, required_approvers, created_at, status,
                current_stage, approvals, comments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow.id,
            workflow.type,
            workflow.title,
            workflow.description,
            workflow.requester,
            workflow.requester_role.value,
            json.dumps(workflow.data),
            workflow.risk_level.value,
            json.dumps([role.value for role in workflow.required_approvers]),
            workflow.created_at.isoformat(),
            workflow.status.value,
            workflow.current_stage,
            json.dumps(workflow.approvals),
            json.dumps(workflow.comments)
        ))
        
        conn.commit()
        conn.close()
    
    async def get_pending_approvals(self, user_id: str) -> List[Dict[str, Any]]:
        """Get pending approval requests for a user."""
        if user_id not in self.users:
            return []
        
        user_role = self.users[user_id]["role"]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM workflows 
            WHERE status = ? AND current_stage < json_array_length(required_approvers)
        """, (WorkflowStatus.AWAITING_APPROVAL.value,))
        
        rows = cursor.fetchall()
        conn.close()
        
        pending = []
        for row in rows:
            required_approvers = json.loads(row[8])
            current_stage = row[11]
            
            # Check if this user's role is required at the current stage
            if (current_stage < len(required_approvers) and 
                UserRole(required_approvers[current_stage]) == user_role):
                
                pending.append({
                    "id": row[0],
                    "type": row[1],
                    "title": row[2],
                    "description": row[3],
                    "requester": row[4],
                    "risk_level": row[7],
                    "created_at": row[9]
                })
        
        return pending
    
    async def approve_workflow(self, workflow_id: str, approver: str, comments: str = "") -> bool:
        """Approve a workflow request."""
        if approver not in self.users:
            return False
        
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return False
        
        # Check if user can approve at current stage
        approver_role = self.users[approver]["role"]
        required_approvers = json.loads(workflow["required_approvers"])
        current_stage = workflow["current_stage"]
        
        if (current_stage >= len(required_approvers) or
            UserRole(required_approvers[current_stage]) != approver_role):
            return False
        
        # Add approval
        approvals = json.loads(workflow["approvals"])
        approvals.append({
            "approver": approver,
            "role": approver_role.value,
            "timestamp": datetime.now().isoformat(),
            "comments": comments
        })
        
        # Update workflow
        current_stage += 1
        status = WorkflowStatus.AWAITING_APPROVAL
        
        # Check if all approvals are complete
        if current_stage >= len(required_approvers):
            status = WorkflowStatus.APPROVED
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE workflows 
            SET current_stage = ?, status = ?, approvals = ?
            WHERE id = ?
        """, (current_stage, status.value, json.dumps(approvals), workflow_id))
        
        conn.commit()
        conn.close()
        
        # Log audit entry
        await self._log_audit(
            workflow_id,
            approver,
            "WORKFLOW_APPROVED",
            f"Approved workflow at stage {current_stage}. Comments: {comments}"
        )
        
        # Send notifications
        if status == WorkflowStatus.APPROVED:
            await self._notify_completion(workflow_id, "approved")
        elif current_stage < len(required_approvers):
            # Notify next approver
            next_role = UserRole(required_approvers[current_stage])
            await self._notify_next_approver(workflow_id, next_role)
        
        logger.info(f"Workflow {workflow_id} approved by {approver} at stage {current_stage}")
        return True
    
    async def reject_workflow(self, workflow_id: str, rejector: str, reason: str) -> bool:
        """Reject a workflow request."""
        if rejector not in self.users:
            return False
        
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return False
        
        # Update workflow status
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE workflows 
            SET status = ?
            WHERE id = ?
        """, (WorkflowStatus.REJECTED.value, workflow_id))
        
        conn.commit()
        conn.close()
        
        # Log audit entry
        await self._log_audit(
            workflow_id,
            rejector,
            "WORKFLOW_REJECTED",
            f"Rejected workflow. Reason: {reason}"
        )
        
        # Send notification
        await self._notify_completion(workflow_id, "rejected", reason)
        
        logger.info(f"Workflow {workflow_id} rejected by {rejector}")
        return True
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow details."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "type": row[1],
            "title": row[2],
            "description": row[3],
            "requester": row[4],
            "requester_role": row[5],
            "data": json.loads(row[6]),
            "risk_level": row[7],
            "required_approvers": json.loads(row[8]),
            "created_at": row[9],
            "status": row[10],
            "current_stage": row[11],
            "approvals": json.loads(row[12]),
            "comments": json.loads(row[13])
        }
    
    async def get_audit_trail(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get audit trail for a workflow."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, action, details, timestamp 
            FROM audit_log 
            WHERE workflow_id = ? 
            ORDER BY timestamp
        """, (workflow_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "user_id": row[0],
                "action": row[1],
                "details": row[2],
                "timestamp": row[3]
            }
            for row in rows
        ]
    
    async def _log_audit(self, workflow_id: str, user_id: str, action: str, details: str):
        """Log audit entry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit_log (workflow_id, user_id, action, details, timestamp, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow_id,
            user_id,
            action,
            details,
            datetime.now().isoformat(),
            "127.0.0.1",  # Mock IP
            "TFrameX Enterprise HITL System"
        ))
        
        conn.commit()
        conn.close()
    
    async def _notify_approvers(self, workflow: WorkflowRequest):
        """Send notifications to required approvers."""
        # For demo purposes, just log notifications
        first_approver_role = workflow.required_approvers[0]
        logger.info(f"📧 Notification sent to {first_approver_role.value} for workflow {workflow.id}")
    
    async def _notify_completion(self, workflow_id: str, status: str, reason: str = ""):
        """Notify workflow completion."""
        logger.info(f"📧 Workflow {workflow_id} {status}. Notifications sent to stakeholders.")
        if reason:
            logger.info(f"   Reason: {reason}")
    
    async def _notify_next_approver(self, workflow_id: str, next_role: UserRole):
        """Notify next approver in chain."""
        logger.info(f"📧 Notification sent to {next_role.value} for workflow {workflow_id}")
    
    async def run_interactive_demo(self):
        """Run interactive enterprise workflow demo."""
        self.app = self._setup_app()
        
        logger.info("🏢 Starting Enterprise Human-in-the-Loop Workflow System...")
        logger.info("🤖 Powered by TFrameX + Advanced AI Agents")
        
        async with self.app.run_context() as ctx:
            print("\n" + "="*80)
            print("🏢 Enterprise Human-in-the-Loop (HITL) Workflow System")
            print("🔹 Powered by TFrameX + Multi-Agent AI + Compliance Framework")
            print("="*80)
            print("\n🎯 Available Agents:")
            print("  • WorkflowCoordinator - Create and manage workflow requests")
            print("  • ApprovalManager     - Process approvals and rejections")  
            print("  • ComplianceOfficer   - Ensure regulatory compliance")
            print("\n💼 Workflow Types:")
            print("  • expense_approval      - Employee expense reimbursements")
            print("  • infrastructure_change - IT system modifications")
            print("  • contract_approval     - Legal contract reviews")
            print("  • customer_escalation   - Customer service escalations")
            print("\n👥 Simulated Users:")
            for user_id, info in self.users.items():
                print(f"  • {user_id} - {info['name']} ({info['role'].value})")
            print("\n💡 Example Commands:")
            print("  • 'Create an expense approval request for $5000 travel costs'")
            print("  • 'Show me pending approvals for sarah.manager'")
            print("  • 'Approve workflow WF-1234567890-1234'")
            print("  • 'Check the status of workflow WF-1234567890-1234'")
            print("  • 'Show audit trail for workflow WF-1234567890-1234'")
            print("\n⚡ Commands:")
            print("  • 'demo' - Run automated demonstration")
            print("  • 'switch' - Change agents")
            print("  • 'exit' - Exit the system")
            print("="*80)
            
            await ctx.interactive_chat(default_agent_name="WorkflowCoordinator")
        
        logger.info("🛑 Shutting down Enterprise Workflow System...")
        logger.info("✅ Shutdown complete!")
    
    async def run_automated_demo(self):
        """Run automated demonstration of enterprise workflows."""
        self.app = self._setup_app()
        
        logger.info("🧪 Running Enterprise HITL Workflow Demonstration...")
        
        async with self.app.run_context() as ctx:
            # Demo scenarios
            demo_scenarios = [
                {
                    "description": "Create a high-value expense approval request",
                    "agent": "WorkflowCoordinator",
                    "message": """Create an expense approval workflow request with these details:
- Title: "Executive Conference Travel Expenses"  
- Description: "Reimbursement for Q4 leadership conference in Singapore including flights, accommodation, and meals"
- Requester: john.doe
- Amount: 15000
- Category: travel
- Business justification: Strategic planning meeting for 2025 roadmap"""
                },
                {
                    "description": "Check pending approvals for manager",
                    "agent": "ApprovalManager",
                    "message": "Show me all pending approval requests for sarah.manager"
                },
                {
                    "description": "Create infrastructure change request",
                    "agent": "WorkflowCoordinator", 
                    "message": """Create an infrastructure change request:
- Title: "Production Database Migration"
- Description: "Migrate customer database from MySQL 5.7 to MySQL 8.0 with zero downtime"
- Requester: tom.itadmin
- Impact: high
- Systems affected: customer_db, analytics_db, reporting_api
- Downtime required: 2 hours maintenance window"""
                },
                {
                    "description": "Review compliance for infrastructure change",
                    "agent": "ComplianceOfficer",
                    "message": "Please review all recent infrastructure change requests for compliance and security considerations"
                }
            ]
            
            for i, scenario in enumerate(demo_scenarios, 1):
                print(f"\n🔍 Demo Scenario {i}: {scenario['description']}")
                print("-" * 60)
                
                response = await ctx.call_agent(
                    scenario['agent'],
                    Message(role="user", content=scenario['message'])
                )
                
                print(f"🤖 {scenario['agent']}: {response.content}")
                print("-" * 60)
                
                # Brief pause between scenarios
                await asyncio.sleep(1)
        
        logger.info("✅ Demo completed successfully!")


async def main():
    """Main application entry point."""
    system = EnterpriseWorkflowSystem()
    
    # Check for demo mode
    if "--demo" in os.sys.argv:
        await system.run_automated_demo()
    else:
        await system.run_interactive_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Application terminated by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}", exc_info=True)
    finally:
        logger.info("🏁 Application exiting")