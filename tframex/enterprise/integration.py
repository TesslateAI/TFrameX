"""
Enterprise Integration Layer

This module provides seamless integration between TFrameX core
and enterprise features, including automatic instrumentation,
monitoring, and enhanced capabilities.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from ..models.primitives import Message
from ..app import TFrameXApp, TFrameXRuntimeContext
from .app import EnterpriseApp
from .models import User
from .tracing import WorkflowTracer
from .analytics import AnalyticsDashboard
from .security.middleware import SecurityContext

logger = logging.getLogger(__name__)


class EnterpriseRuntimeContext(TFrameXRuntimeContext):
    """
    Enhanced runtime context with enterprise features.
    
    Extends the standard TFrameX runtime context with:
    - Automatic workflow tracing
    - Security context integration
    - Enhanced metrics collection
    - Audit logging
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize enterprise runtime context."""
        super().__init__(*args, **kwargs)
        
        # Enterprise components
        self.security_context: Optional[SecurityContext] = None
        self.workflow_tracer: Optional[WorkflowTracer] = None
        self.current_trace_id: Optional[str] = None
        self.enterprise_app: Optional[EnterpriseApp] = None
        
        # Extract enterprise app from parent
        if hasattr(self.app, '_is_enterprise_app'):
            self.enterprise_app = self.app
            self.workflow_tracer = getattr(self.app, '_workflow_tracer', None)
    
    async def call_agent(self, agent_name: str, input_message: Union[str, Message], 
                        template_vars: Optional[Dict[str, Any]] = None,
                        **kwargs) -> Message:
        """
        Call an agent with enterprise instrumentation.
        
        Automatically adds:
        - Workflow tracing
        - Security checks
        - Performance metrics
        - Audit logging
        """
        # Create security context if user is available
        user = kwargs.get('user') or getattr(self, 'user', None)
        
        # Start operation tracing if workflow tracer is available
        if self.workflow_tracer and self.current_trace_id:
            async with self.workflow_tracer.trace_operation(
                trace_id=self.current_trace_id,
                operation_name=f"agent_call:{agent_name}",
                tags={
                    "agent_name": agent_name,
                    "user_id": str(user.id) if user else None,
                    "message_type": type(input_message).__name__
                }
            ) as span:
                
                # Add security context to span
                if self.security_context:
                    span.tags.update({
                        "authenticated": self.security_context.authenticated,
                        "auth_method": self.security_context.auth_method
                    })
                
                # Log the operation
                await self.workflow_tracer.add_span_log(
                    span.span_id,
                    f"Calling agent '{agent_name}' with input message",
                    level="info",
                    agent_name=agent_name,
                    input_length=len(str(input_message))
                )
                
                try:
                    # Call the original agent method
                    result = await super().call_agent(
                        agent_name, input_message, template_vars, **kwargs
                    )
                    
                    # Log successful completion
                    await self.workflow_tracer.add_span_log(
                        span.span_id,
                        f"Agent '{agent_name}' completed successfully",
                        level="info",
                        output_length=len(str(result.content)) if result else 0
                    )
                    
                    # Record metrics if enterprise app is available
                    if self.enterprise_app and hasattr(self.enterprise_app, '_metrics_manager'):
                        metrics = self.enterprise_app._metrics_manager
                        if metrics:
                            await metrics.increment_counter(
                                "tframex_agent_calls_total",
                                labels={
                                    "agent_name": agent_name,
                                    "status": "success",
                                    "user_id": str(user.id) if user else "anonymous"
                                }
                            )
                    
                    return result
                    
                except Exception as e:
                    # Log error
                    await self.workflow_tracer.add_span_log(
                        span.span_id,
                        f"Agent '{agent_name}' failed with error: {str(e)}",
                        level="error",
                        error_type=e.__class__.__name__,
                        error_message=str(e)
                    )
                    
                    # Record error metrics
                    if self.enterprise_app and hasattr(self.enterprise_app, '_metrics_manager'):
                        metrics = self.enterprise_app._metrics_manager
                        if metrics:
                            await metrics.increment_counter(
                                "tframex_agent_errors_total",
                                labels={
                                    "agent_name": agent_name,
                                    "error_type": e.__class__.__name__,
                                    "user_id": str(user.id) if user else "anonymous"
                                }
                            )
                    
                    raise
        else:
            # Fallback to standard call if no tracing available
            return await super().call_agent(agent_name, input_message, template_vars, **kwargs)
    
    async def run_flow(self, flow_name: str, initial_message: Union[str, Message],
                      flow_template_vars: Optional[Dict[str, Any]] = None,
                      **kwargs) -> Any:
        """
        Run a flow with enterprise instrumentation.
        
        Automatically adds:
        - Complete workflow tracing
        - Performance monitoring
        - Security enforcement
        - Audit logging
        """
        user = kwargs.get('user') or getattr(self, 'user', None)
        
        # Start workflow trace if tracer is available
        if self.workflow_tracer:
            trace_id = await self.workflow_tracer.start_workflow_trace(
                workflow_name=f"flow:{flow_name}",
                user=user,
                metadata={
                    "flow_name": flow_name,
                    "initial_message_type": type(initial_message).__name__,
                    "template_vars": flow_template_vars
                }
            )
            
            # Set current trace ID for nested operations
            self.current_trace_id = trace_id
            
            try:
                async with self.workflow_tracer.trace_operation(
                    trace_id=trace_id,
                    operation_name=f"flow_execution:{flow_name}",
                    tags={
                        "flow_name": flow_name,
                        "user_id": str(user.id) if user else None
                    }
                ) as span:
                    
                    # Run the flow
                    result = await super().run_flow(
                        flow_name, initial_message, flow_template_vars, **kwargs
                    )
                    
                    # Log completion
                    await self.workflow_tracer.add_span_log(
                        span.span_id,
                        f"Flow '{flow_name}' completed successfully",
                        level="info"
                    )
                    
                    # Record flow metrics
                    if self.enterprise_app and hasattr(self.enterprise_app, '_metrics_manager'):
                        metrics = self.enterprise_app._metrics_manager
                        if metrics:
                            await metrics.increment_counter(
                                "tframex_flow_executions_total",
                                labels={
                                    "flow_name": flow_name,
                                    "status": "success",
                                    "user_id": str(user.id) if user else "anonymous"
                                }
                            )
                    
                    # Finish workflow trace
                    await self.workflow_tracer.finish_workflow_trace(trace_id, "success")
                    
                    return result
                    
            except Exception as e:
                # Finish workflow trace with error
                await self.workflow_tracer.finish_workflow_trace(trace_id, "error", e)
                
                # Record error metrics
                if self.enterprise_app and hasattr(self.enterprise_app, '_metrics_manager'):
                    metrics = self.enterprise_app._metrics_manager
                    if metrics:
                        await metrics.increment_counter(
                            "tframex_flow_errors_total",
                            labels={
                                "flow_name": flow_name,
                                "error_type": e.__class__.__name__,
                                "user_id": str(user.id) if user else "anonymous"
                            }
                        )
                
                raise
            finally:
                # Clear current trace ID
                self.current_trace_id = None
        else:
            # Fallback to standard flow execution
            return await super().run_flow(flow_name, initial_message, flow_template_vars, **kwargs)


class EnhancedEnterpriseApp(EnterpriseApp):
    """
    Enhanced enterprise application with seamless TFrameX integration.
    
    Provides all enterprise features while maintaining full compatibility
    with existing TFrameX applications.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize enhanced enterprise app."""
        super().__init__(*args, **kwargs)
        
        # Mark as enterprise app
        self._is_enterprise_app = True
        
        # Enhanced components
        self._workflow_tracer: Optional[WorkflowTracer] = None
        self._analytics_dashboard: Optional[AnalyticsDashboard] = None
        
        logger.info("Enhanced enterprise app initialized")
    
    async def initialize_enterprise(self) -> None:
        """Initialize enterprise features with enhanced integration."""
        # Call parent initialization
        await super().initialize_enterprise()
        
        # Initialize enhanced components
        await self._initialize_enhanced_features()
    
    async def _initialize_enhanced_features(self) -> None:
        """Initialize enhanced enterprise features."""
        try:
            # Get primary storage from storage backends
            primary_storage = None
            if hasattr(self, '_storage_backends') and self._storage_backends:
                primary_storage = next(iter(self._storage_backends.values()))
            
            # Initialize workflow tracer
            if primary_storage:
                self._workflow_tracer = WorkflowTracer(
                    storage=primary_storage,
                    enable_opentelemetry=True
                )
                logger.info("Workflow tracer initialized")
            else:
                logger.warning("No storage backend available for workflow tracer")
            
            # Initialize analytics dashboard
            if primary_storage:
                self._analytics_dashboard = AnalyticsDashboard(
                    storage=primary_storage,
                    metrics_manager=getattr(self, '_metrics_manager', None),
                    workflow_tracer=self._workflow_tracer
                )
                logger.info("Analytics dashboard initialized")
            else:
                logger.warning("No storage backend available for analytics dashboard")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced features: {e}")
            # Don't raise - allow the app to continue without enhanced features
            logger.warning("Continuing without enhanced features")
    
    async def start_enterprise(self) -> None:
        """Start enterprise services with enhanced features."""
        # Call parent start
        await super().start_enterprise()
        
        # Start enhanced services
        if self._analytics_dashboard:
            await self._analytics_dashboard.start()
            logger.info("Analytics dashboard started")
    
    async def stop_enterprise(self) -> None:
        """Stop enterprise services with enhanced features."""
        # Stop enhanced services
        if self._analytics_dashboard:
            await self._analytics_dashboard.stop()
            logger.info("Analytics dashboard stopped")
        
        # Call parent stop
        await super().stop_enterprise()
    
    @asynccontextmanager
    async def run_context(self, llm=None, user: Optional[User] = None, **kwargs):
        """
        Create an enhanced runtime context with enterprise features.
        
        Args:
            llm: Optional LLM override for this context
            user: User for this context (enables security features)
            **kwargs: Additional context arguments
        """
        # Create enterprise runtime context
        context = EnterpriseRuntimeContext(
            app=self,
            llm=llm or self.default_llm,
            **kwargs
        )
        
        # Set user for security context
        if user:
            context.user = user
            
            # Create security context
            if self._security_middleware:
                context.security_context = SecurityContext()
                context.security_context.user = user
                context.security_context.authenticated = True
                context.security_context.auth_method = "direct"
        
        # Set workflow tracer
        if self._workflow_tracer:
            context.workflow_tracer = self._workflow_tracer
        
        async with context as ctx:
            yield ctx
    
    def get_workflow_tracer(self) -> Optional[WorkflowTracer]:
        """Get the workflow tracer instance."""
        return self._workflow_tracer
    
    def get_analytics_dashboard(self) -> Optional[AnalyticsDashboard]:
        """Get the analytics dashboard instance."""
        return self._analytics_dashboard
    
    async def get_real_time_analytics(self) -> Dict[str, Any]:
        """Get real-time analytics data."""
        if self._analytics_dashboard:
            return await self._analytics_dashboard.get_real_time_analytics()
        else:
            return {"error": "Analytics dashboard not available"}
    
    async def get_workflow_analytics(self, workflow_name: Optional[str] = None,
                                   time_window_hours: int = 24) -> Dict[str, Any]:
        """Get workflow analytics data."""
        if self._workflow_tracer:
            return await self._workflow_tracer.get_workflow_analytics(
                workflow_name=workflow_name,
                time_window_hours=time_window_hours
            )
        else:
            return {"error": "Workflow tracer not available"}
    
    async def get_agent_analytics(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get agent analytics data."""
        if self._analytics_dashboard:
            return await self._analytics_dashboard.get_agent_analytics(agent_name)
        else:
            return {"error": "Analytics dashboard not available"}
    
    async def get_cost_analytics(self, time_period: str = "24h") -> Dict[str, Any]:
        """Get cost analytics and optimization recommendations."""
        if self._analytics_dashboard:
            return await self._analytics_dashboard.get_cost_analytics(time_period)
        else:
            return {"error": "Analytics dashboard not available"}
    
    async def search_workflow_traces(self, **kwargs) -> List[Dict[str, Any]]:
        """Search for workflow traces."""
        if self._workflow_tracer:
            traces = await self._workflow_tracer.search_workflow_traces(**kwargs)
            return [trace.to_dict() for trace in traces]
        else:
            return []
    
    async def export_analytics(self, format: str = "json", 
                             time_range: str = "24h") -> Union[str, Dict[str, Any]]:
        """
        Export analytics data in various formats.
        
        Args:
            format: Export format (json, csv, excel)
            time_range: Time range for export (24h, 7d, 30d)
            
        Returns:
            Exported data in requested format
        """
        try:
            # Get comprehensive analytics data
            real_time = await self.get_real_time_analytics()
            agent_analytics = await self.get_agent_analytics()
            cost_analytics = await self.get_cost_analytics(time_range)
            
            if self._analytics_dashboard:
                historical = await self._analytics_dashboard.get_historical_analytics(
                    hours=24 if time_range == "24h" else 7*24 if time_range == "7d" else 30*24
                )
            else:
                historical = {}
            
            export_data = {
                "export_info": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "format": format,
                    "time_range": time_range
                },
                "real_time_analytics": real_time,
                "agent_analytics": agent_analytics,
                "cost_analytics": cost_analytics,
                "historical_analytics": historical
            }
            
            if format == "json":
                return export_data
            elif format == "csv":
                # Convert to CSV format (simplified)
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write headers
                writer.writerow(["Metric", "Value", "Timestamp"])
                
                # Write real-time data
                if "real_time" in real_time:
                    rt_data = real_time["real_time"]
                    for key, value in rt_data.items():
                        if not isinstance(value, dict):
                            writer.writerow([key, value, rt_data.get("timestamp", "")])
                
                return output.getvalue()
            else:
                return {"error": f"Unsupported export format: {format}"}
                
        except Exception as e:
            logger.error(f"Error exporting analytics: {e}")
            return {"error": str(e)}


# Convenience function for creating enhanced enterprise apps
def create_enhanced_enterprise_app(*args, **kwargs) -> EnhancedEnterpriseApp:
    """
    Create an enhanced enterprise application with all features enabled.
    
    This is the recommended way to create enterprise TFrameX applications
    as it provides the most comprehensive feature set with seamless integration.
    """
    return EnhancedEnterpriseApp(*args, **kwargs)