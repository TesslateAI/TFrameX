"""
Enterprise Analytics Dashboard

This module provides comprehensive analytics and insights for
TFrameX enterprise deployments with real-time monitoring capabilities.
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .models import User
from .storage.base import BaseStorage
from .metrics.manager import MetricsManager
from .tracing import WorkflowTracer

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsSnapshot:
    """Snapshot of analytics data at a specific point in time."""
    timestamp: datetime
    total_requests: int
    success_rate: float
    avg_response_time_ms: float
    active_users: int
    error_rate: float
    throughput_per_minute: float
    cost_data: Dict[str, Any] = field(default_factory=dict)
    agent_performance: Dict[str, Any] = field(default_factory=dict)
    resource_utilization: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_requests": self.total_requests,
            "success_rate": self.success_rate,
            "avg_response_time_ms": self.avg_response_time_ms,
            "active_users": self.active_users,
            "error_rate": self.error_rate,
            "throughput_per_minute": self.throughput_per_minute,
            "cost_data": self.cost_data,
            "agent_performance": self.agent_performance,
            "resource_utilization": self.resource_utilization
        }


@dataclass
class AgentAnalytics:
    """Analytics data for a specific agent."""
    agent_name: str
    total_calls: int
    success_calls: int
    failed_calls: int
    avg_duration_ms: float
    total_tokens: int
    total_cost_usd: float
    last_called: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        return (self.success_calls / self.total_calls * 100) if self.total_calls > 0 else 0
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        return (self.failed_calls / self.total_calls * 100) if self.total_calls > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_name": self.agent_name,
            "total_calls": self.total_calls,
            "success_calls": self.success_calls,
            "failed_calls": self.failed_calls,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "avg_duration_ms": self.avg_duration_ms,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "last_called": self.last_called.isoformat() if self.last_called else None
        }


class AnalyticsDashboard:
    """
    Enterprise analytics dashboard providing real-time insights and monitoring.
    
    Features:
    - Real-time performance monitoring
    - Agent performance analytics
    - Cost tracking and optimization
    - Resource utilization monitoring
    - Alerting and anomaly detection
    - Historical trend analysis
    """
    
    def __init__(self, storage: BaseStorage, 
                 metrics_manager: Optional[MetricsManager] = None,
                 workflow_tracer: Optional[WorkflowTracer] = None):
        """
        Initialize analytics dashboard.
        
        Args:
            storage: Storage backend for analytics data
            metrics_manager: Metrics manager for real-time metrics
            workflow_tracer: Workflow tracer for execution analytics
        """
        self.storage = storage
        self.metrics_manager = metrics_manager
        self.workflow_tracer = workflow_tracer
        
        # In-memory analytics cache
        self._analytics_cache: Dict[str, Any] = {}
        self._agent_analytics: Dict[str, AgentAnalytics] = {}
        self._snapshots: List[AnalyticsSnapshot] = []
        
        # Configuration
        self.snapshot_interval_minutes = 5
        self.max_snapshots = 288  # 24 hours of 5-minute snapshots
        self.cache_ttl_seconds = 30
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._running = False
        
        logger.info("Analytics dashboard initialized")
    
    async def start(self) -> None:
        """Start the analytics dashboard background services."""
        if self._running:
            return
        
        self._running = True
        
        # Start background data collection
        snapshot_task = asyncio.create_task(self._snapshot_collector())
        cache_task = asyncio.create_task(self._cache_updater())
        
        self._background_tasks = [snapshot_task, cache_task]
        
        logger.info("Analytics dashboard services started")
    
    async def stop(self) -> None:
        """Stop the analytics dashboard background services."""
        self._running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self._background_tasks.clear()
        
        logger.info("Analytics dashboard services stopped")
    
    async def _snapshot_collector(self) -> None:
        """Background task to collect analytics snapshots."""
        while self._running:
            try:
                snapshot = await self._create_analytics_snapshot()
                
                # Add to in-memory snapshots
                self._snapshots.append(snapshot)
                
                # Keep only recent snapshots
                if len(self._snapshots) > self.max_snapshots:
                    self._snapshots = self._snapshots[-self.max_snapshots:]
                
                # Persist snapshot
                await self.storage.insert("analytics_snapshots", snapshot.to_dict())
                
                logger.debug(f"Analytics snapshot collected: {snapshot.timestamp}")
                
            except Exception as e:
                logger.error(f"Error collecting analytics snapshot: {e}")
            
            # Wait for next interval
            await asyncio.sleep(self.snapshot_interval_minutes * 60)
    
    async def _cache_updater(self) -> None:
        """Background task to update analytics cache."""
        while self._running:
            try:
                # Update agent analytics
                await self._update_agent_analytics()
                
                # Update general analytics cache
                await self._update_analytics_cache()
                
                logger.debug("Analytics cache updated")
                
            except Exception as e:
                logger.error(f"Error updating analytics cache: {e}")
            
            # Wait for next update
            await asyncio.sleep(self.cache_ttl_seconds)
    
    async def _create_analytics_snapshot(self) -> AnalyticsSnapshot:
        """Create a new analytics snapshot."""
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        
        try:
            # Get recent audit logs for metrics
            audit_logs = await self.storage.select(
                "audit_logs",
                filters={"timestamp": {"$gte": one_hour_ago.isoformat()}},
                limit=10000
            )
            
            # Calculate metrics
            total_requests = len(audit_logs)
            successful_requests = len([log for log in audit_logs if log.get("outcome") == "success"])
            
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            error_rate = 100 - success_rate
            
            # Calculate response times (if available)
            response_times = []
            for log in audit_logs:
                if "duration_ms" in log.get("details", {}):
                    response_times.append(log["details"]["duration_ms"])
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Calculate throughput
            throughput_per_minute = total_requests / 60 if total_requests > 0 else 0
            
            # Get active users
            unique_users = set()
            for log in audit_logs:
                if log.get("user_id"):
                    unique_users.add(log["user_id"])
            active_users = len(unique_users)
            
            # Agent performance data
            agent_performance = await self._calculate_agent_performance(audit_logs)
            
            # Cost data (placeholder - would integrate with actual cost tracking)
            cost_data = await self._calculate_cost_data(audit_logs)
            
            # Resource utilization (placeholder)
            resource_utilization = {
                "cpu_percent": 0,  # Would integrate with system metrics
                "memory_percent": 0,
                "storage_used_gb": 0
            }
            
            return AnalyticsSnapshot(
                timestamp=now,
                total_requests=total_requests,
                success_rate=success_rate,
                avg_response_time_ms=avg_response_time,
                active_users=active_users,
                error_rate=error_rate,
                throughput_per_minute=throughput_per_minute,
                cost_data=cost_data,
                agent_performance=agent_performance,
                resource_utilization=resource_utilization
            )
            
        except Exception as e:
            logger.error(f"Error creating analytics snapshot: {e}")
            # Return empty snapshot
            return AnalyticsSnapshot(
                timestamp=now,
                total_requests=0,
                success_rate=0,
                avg_response_time_ms=0,
                active_users=0,
                error_rate=0,
                throughput_per_minute=0
            )
    
    async def _calculate_agent_performance(self, audit_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate agent performance metrics from audit logs."""
        agent_stats = defaultdict(lambda: {
            "calls": 0, "successes": 0, "failures": 0, 
            "total_duration": 0, "response_times": []
        })
        
        for log in audit_logs:
            if log.get("resource") == "agent":
                agent_name = log.get("details", {}).get("agent_name", "unknown")
                stats = agent_stats[agent_name]
                
                stats["calls"] += 1
                if log.get("outcome") == "success":
                    stats["successes"] += 1
                else:
                    stats["failures"] += 1
                
                if "duration_ms" in log.get("details", {}):
                    duration = log["details"]["duration_ms"]
                    stats["total_duration"] += duration
                    stats["response_times"].append(duration)
        
        # Convert to final format
        performance = {}
        for agent_name, stats in agent_stats.items():
            avg_duration = stats["total_duration"] / stats["calls"] if stats["calls"] > 0 else 0
            success_rate = stats["successes"] / stats["calls"] * 100 if stats["calls"] > 0 else 0
            
            performance[agent_name] = {
                "total_calls": stats["calls"],
                "success_rate": success_rate,
                "avg_duration_ms": avg_duration,
                "p95_duration_ms": self._calculate_percentile(stats["response_times"], 95) if stats["response_times"] else 0
            }
        
        return performance
    
    async def _calculate_cost_data(self, audit_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cost data from audit logs."""
        # Placeholder cost calculation
        # In real implementation, would integrate with LLM provider billing APIs
        
        total_tokens = 0
        total_api_calls = 0
        
        for log in audit_logs:
            details = log.get("details", {})
            if "tokens_used" in details:
                total_tokens += details["tokens_used"]
            if log.get("resource") == "agent":
                total_api_calls += 1
        
        # Estimated costs (placeholder rates)
        estimated_token_cost = total_tokens * 0.00002  # $0.02 per 1K tokens
        estimated_api_cost = total_api_calls * 0.001   # $0.001 per API call
        total_estimated_cost = estimated_token_cost + estimated_api_cost
        
        return {
            "total_tokens": total_tokens,
            "total_api_calls": total_api_calls,
            "estimated_cost_usd": total_estimated_cost,
            "cost_breakdown": {
                "tokens": estimated_token_cost,
                "api_calls": estimated_api_cost
            }
        }
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of a list of values."""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    async def _update_agent_analytics(self) -> None:
        """Update agent analytics from recent data."""
        try:
            # Get recent audit logs for agents
            one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
            audit_logs = await self.storage.select(
                "audit_logs",
                filters={
                    "resource": "agent",
                    "timestamp": {"$gte": one_day_ago.isoformat()}
                },
                limit=10000
            )
            
            # Reset agent analytics
            self._agent_analytics.clear()
            
            # Process audit logs
            for log in audit_logs:
                agent_name = log.get("details", {}).get("agent_name", "unknown")
                
                if agent_name not in self._agent_analytics:
                    self._agent_analytics[agent_name] = AgentAnalytics(
                        agent_name=agent_name,
                        total_calls=0,
                        success_calls=0,
                        failed_calls=0,
                        avg_duration_ms=0,
                        total_tokens=0,
                        total_cost_usd=0
                    )
                
                analytics = self._agent_analytics[agent_name]
                analytics.total_calls += 1
                
                if log.get("outcome") == "success":
                    analytics.success_calls += 1
                else:
                    analytics.failed_calls += 1
                
                # Update last called time
                log_time = datetime.fromisoformat(log["timestamp"])
                if not analytics.last_called or log_time > analytics.last_called:
                    analytics.last_called = log_time
                
                # Update tokens and cost if available
                details = log.get("details", {})
                if "tokens_used" in details:
                    analytics.total_tokens += details["tokens_used"]
                if "cost_usd" in details:
                    analytics.total_cost_usd += details["cost_usd"]
            
            # Calculate average durations
            for agent_name, analytics in self._agent_analytics.items():
                # Get duration data from audit logs
                durations = []
                for log in audit_logs:
                    if (log.get("details", {}).get("agent_name") == agent_name and
                        "duration_ms" in log.get("details", {})):
                        durations.append(log["details"]["duration_ms"])
                
                if durations:
                    analytics.avg_duration_ms = sum(durations) / len(durations)
            
        except Exception as e:
            logger.error(f"Error updating agent analytics: {e}")
    
    async def _update_analytics_cache(self) -> None:
        """Update general analytics cache."""
        try:
            # Create current snapshot without persisting
            current_snapshot = await self._create_analytics_snapshot()
            
            # Update cache
            self._analytics_cache["current"] = current_snapshot.to_dict()
            self._analytics_cache["last_updated"] = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            logger.error(f"Error updating analytics cache: {e}")
    
    async def get_real_time_analytics(self) -> Dict[str, Any]:
        """
        Get real-time analytics data.
        
        Returns:
            Real-time analytics including performance metrics, agent data, etc.
        """
        try:
            # Return cached data if available and recent
            if "current" in self._analytics_cache:
                last_updated = datetime.fromisoformat(self._analytics_cache["last_updated"])
                if (datetime.now(timezone.utc) - last_updated).seconds < self.cache_ttl_seconds:
                    return {
                        "real_time": self._analytics_cache["current"],
                        "agents": {name: analytics.to_dict() for name, analytics in self._agent_analytics.items()},
                        "cache_hit": True
                    }
            
            # Generate fresh data
            current_snapshot = await self._create_analytics_snapshot()
            
            return {
                "real_time": current_snapshot.to_dict(),
                "agents": {name: analytics.to_dict() for name, analytics in self._agent_analytics.items()},
                "cache_hit": False
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time analytics: {e}")
            return {"error": str(e)}
    
    async def get_historical_analytics(self, 
                                     hours: int = 24,
                                     granularity: str = "hourly") -> Dict[str, Any]:
        """
        Get historical analytics data.
        
        Args:
            hours: Number of hours of history to include
            granularity: Data granularity (hourly, daily)
            
        Returns:
            Historical analytics data
        """
        try:
            since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            # Get snapshots from storage
            snapshots = await self.storage.select(
                "analytics_snapshots",
                filters={"timestamp": {"$gte": since_time.isoformat()}},
                order_by="timestamp",
                limit=1000
            )
            
            # Aggregate by granularity
            if granularity == "hourly":
                aggregated = self._aggregate_snapshots_hourly(snapshots)
            else:
                aggregated = snapshots  # Return raw data for now
            
            return {
                "time_range": {
                    "start": since_time.isoformat(),
                    "end": datetime.now(timezone.utc).isoformat(),
                    "hours": hours
                },
                "granularity": granularity,
                "data_points": len(aggregated),
                "snapshots": aggregated
            }
            
        except Exception as e:
            logger.error(f"Error getting historical analytics: {e}")
            return {"error": str(e)}
    
    def _aggregate_snapshots_hourly(self, snapshots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate snapshots by hour."""
        hourly_buckets = defaultdict(list)
        
        for snapshot in snapshots:
            timestamp = datetime.fromisoformat(snapshot["timestamp"])
            hour_key = timestamp.replace(minute=0, second=0, microsecond=0).isoformat()
            hourly_buckets[hour_key].append(snapshot)
        
        aggregated = []
        for hour_key, hour_snapshots in sorted(hourly_buckets.items()):
            # Calculate averages for the hour
            avg_snapshot = {
                "timestamp": hour_key,
                "total_requests": sum(s["total_requests"] for s in hour_snapshots),
                "success_rate": sum(s["success_rate"] for s in hour_snapshots) / len(hour_snapshots),
                "avg_response_time_ms": sum(s["avg_response_time_ms"] for s in hour_snapshots) / len(hour_snapshots),
                "active_users": max(s["active_users"] for s in hour_snapshots),
                "error_rate": sum(s["error_rate"] for s in hour_snapshots) / len(hour_snapshots),
                "throughput_per_minute": sum(s["throughput_per_minute"] for s in hour_snapshots) / len(hour_snapshots),
                "data_points": len(hour_snapshots)
            }
            aggregated.append(avg_snapshot)
        
        return aggregated
    
    async def get_agent_analytics(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get analytics for specific agent or all agents.
        
        Args:
            agent_name: Specific agent name (or all if None)
            
        Returns:
            Agent analytics data
        """
        try:
            if agent_name:
                if agent_name in self._agent_analytics:
                    return self._agent_analytics[agent_name].to_dict()
                else:
                    return {"error": f"Agent '{agent_name}' not found"}
            else:
                return {
                    "agents": {name: analytics.to_dict() 
                             for name, analytics in self._agent_analytics.items()},
                    "total_agents": len(self._agent_analytics)
                }
                
        except Exception as e:
            logger.error(f"Error getting agent analytics: {e}")
            return {"error": str(e)}
    
    async def get_cost_analytics(self, time_period: str = "24h") -> Dict[str, Any]:
        """
        Get cost analytics and optimization recommendations.
        
        Args:
            time_period: Time period for analysis (24h, 7d, 30d)
            
        Returns:
            Cost analytics with optimization recommendations
        """
        try:
            # Parse time period
            if time_period == "24h":
                hours = 24
            elif time_period == "7d":
                hours = 24 * 7
            elif time_period == "30d":
                hours = 24 * 30
            else:
                hours = 24
            
            since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            # Get audit logs for cost analysis
            audit_logs = await self.storage.select(
                "audit_logs",
                filters={"timestamp": {"$gte": since_time.isoformat()}},
                limit=10000
            )
            
            # Calculate costs by agent
            agent_costs = defaultdict(lambda: {"tokens": 0, "calls": 0, "cost": 0})
            total_cost = 0
            
            for log in audit_logs:
                if log.get("resource") == "agent":
                    agent_name = log.get("details", {}).get("agent_name", "unknown")
                    details = log.get("details", {})
                    
                    agent_costs[agent_name]["calls"] += 1
                    
                    if "tokens_used" in details:
                        tokens = details["tokens_used"]
                        agent_costs[agent_name]["tokens"] += tokens
                        
                        # Estimate cost (placeholder rates)
                        cost = tokens * 0.00002
                        agent_costs[agent_name]["cost"] += cost
                        total_cost += cost
            
            # Generate optimization recommendations
            recommendations = []
            
            # Find high-cost, low-efficiency agents
            for agent_name, costs in agent_costs.items():
                if costs["calls"] > 0:
                    cost_per_call = costs["cost"] / costs["calls"]
                    tokens_per_call = costs["tokens"] / costs["calls"]
                    
                    if cost_per_call > 0.01:  # High cost per call
                        recommendations.append({
                            "type": "high_cost_agent",
                            "agent": agent_name,
                            "message": f"Agent '{agent_name}' has high cost per call (${cost_per_call:.4f})",
                            "suggestion": "Consider optimizing prompts or using a cheaper model"
                        })
                    
                    if tokens_per_call > 1000:  # High token usage
                        recommendations.append({
                            "type": "high_token_usage",
                            "agent": agent_name,
                            "message": f"Agent '{agent_name}' uses many tokens per call ({tokens_per_call:.0f})",
                            "suggestion": "Consider reducing prompt length or output requirements"
                        })
            
            return {
                "time_period": time_period,
                "total_cost_usd": total_cost,
                "agent_breakdown": dict(agent_costs),
                "recommendations": recommendations,
                "cost_trends": {
                    "daily_average": total_cost / (hours / 24),
                    "projected_monthly": total_cost * (30 * 24 / hours)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting cost analytics: {e}")
            return {"error": str(e)}